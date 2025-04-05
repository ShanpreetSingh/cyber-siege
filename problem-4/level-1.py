#!/usr/bin/env python3
"""
SSH Brute Force Protection - Linux Implementation

Monitors SSH login attempts and blocks suspicious IPs using iptables or ufw.
"""

import os
import re
import sys
import time
import signal
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, List, Dict
import threading

# -------------------- Logging Configuration -------------------- #
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ssh-brute-force-blocker")


# -------------------- Log Monitor -------------------- #
class LogMonitor:
    """
    Monitors system logs for SSH authentication failures.
    Supports both /var/log/auth.log and journalctl.
    """

    LOG_PATTERNS = {
        'file': re.compile(
            r'(\w{3}\s+\d+\s+\d+:\d+:\d+).*sshd\[\d+\]:\s+(Failed password|Invalid user).*from\s+(\d+\.\d+\.\d+\.\d+)'
        ),
        'journalctl': re.compile(
            r'(\d+-\d+-\d+\s+\d+:\d+:\d+).*sshd\[\d+\]:\s+(Failed password|Invalid user).*from\s+(\d+\.\d+\.\d+\.\d+)'
        )
    }

    TIMESTAMP_FORMATS = {
        'file': '%Y %b %d %H:%M:%S',
        'journalctl': '%Y-%m-%d %H:%M:%S'
    }

    def __init__(self, threat_detector):
        self.threat_detector = threat_detector
        self.log_file_path = '/var/log/auth.log'
        self.running = False
        self.monitoring_thread = None
        self.monitor_methods = {
            'file': self._monitor_auth_log,
            'journalctl': self._monitor_journalctl
        }

    def _test_log_access(self) -> str:
        """Check which log system is available: file or journalctl."""
        try:
            with open(self.log_file_path, 'r'):
                return 'file'
        except Exception:
            pass

        try:
            subprocess.run(['journalctl', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return 'journalctl'
        except Exception:
            logger.error("Could not access auth.log or journalctl.")
            sys.exit(1)

    def _monitor_auth_log(self):
        """Tail the auth.log file for SSH failures."""
        try:
            with open(self.log_file_path, 'r') as f:
                f.seek(0, 2)  # Move to end of file
                while self.running:
                    line = f.readline()
                    self._process_line_or_sleep(line, 'file')
        except Exception as e:
            logger.error(f"Error reading auth.log: {e}")
            self.running = False

    def _monitor_journalctl(self):
        """Monitor SSH log via journalctl command."""
        try:
            process = subprocess.Popen(
                ['journalctl', '-f', '-u', 'ssh', '-u', 'sshd', '--no-pager'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            while self.running:
                line = process.stdout.readline()
                self._process_line_or_sleep(line, 'journalctl')
            process.terminate()
        except Exception as e:
            logger.error(f"Error reading journalctl: {e}")
            self.running = False

    def _process_line_or_sleep(self, line: str, source_type: str):
        """Process log line or wait briefly if nothing new."""
        if line:
            self._process_log_line(line, source_type)
        else:
            time.sleep(0.1)

    def _parse_timestamp(self, ts: str, source_type: str) -> Optional[datetime]:
        """Convert timestamp string to datetime object."""
        try:
            fmt = self.TIMESTAMP_FORMATS[source_type]
            if source_type == 'file':
                ts = f"{datetime.now().year} {ts}"
            parsed = datetime.strptime(ts, fmt)
            # Fix for possible year rollover
            if source_type == 'file' and parsed > datetime.now() + timedelta(days=1):
                parsed = parsed.replace(year=parsed.year - 1)
            return parsed
        except Exception:
            logger.warning(f"Invalid timestamp: {ts}")
            return None

    def _process_log_line(self, line: str, source_type: str):
        """Extract and handle IPs from failed logins."""
        match = self.LOG_PATTERNS[source_type].search(line)
        if not match:
            return

        timestamp_str, _, ip = match.groups()
        timestamp = self._parse_timestamp(timestamp_str, source_type)
        if timestamp:
            self.threat_detector.register_failure(ip, timestamp)

    def start(self):
        """Begin monitoring SSH logs."""
        if self.running:
            logger.warning("Log monitoring already running.")
            return

        log_source = self._test_log_access()
        self.running = True
        logger.info(f"Monitoring SSH logs using {log_source}")

        self.monitoring_thread = threading.Thread(target=self.monitor_methods[log_source])
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def stop(self):
        """Stop monitoring logs gracefully."""
        self.running = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
        logger.info("Stopped monitoring SSH logs.")


# -------------------- Threat Detection -------------------- #
class ThreatDetector:
    """Tracks failed login attempts and blocks IPs when thresholds are exceeded."""

    def __init__(self, threshold: int, interval: int, whitelist: List[str]):
        self.threshold = threshold
        self.interval = interval
        self.whitelist = set(whitelist)
        self.firewall_manager = None
        self.failures: Dict[str, List[datetime]] = defaultdict(list)
        self.blocked_ips: set = set()

    def set_firewall_manager(self, firewall_manager):
        self.firewall_manager = firewall_manager

    def register_failure(self, ip: str, timestamp: datetime):
        if ip in self.whitelist or ip in self.blocked_ips:
            return

        self.failures[ip].append(timestamp)

        cutoff = datetime.now() - timedelta(seconds=self.interval)
        self.failures[ip] = [t for t in self.failures[ip] if t > cutoff]

        if len(self.failures[ip]) >= self.threshold and self.firewall_manager:
            logger.warning(f"Blocking {ip}: {len(self.failures[ip])} failures in {self.interval}s")
            if self.firewall_manager.block_ip(ip):
                self.blocked_ips.add(ip)
                self.failures[ip] = []


# -------------------- Firewall Manager -------------------- #
class FirewallManager:
    """Handles blocking of IPs using iptables or ufw."""

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.firewall_type = self._detect_firewall()

    def _detect_firewall(self) -> Optional[str]:
        fw_options = [
            ('ufw', ['ufw', 'status'], lambda o: 'Status: active' in o),
            ('iptables', ['iptables', '--version'], lambda o: True),
        ]

        for fw, cmd, check in fw_options:
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0 and check(result.stdout):
                    logger.info(f"Firewall detected: {fw}")
                    return fw
            except Exception:
                continue

        logger.error("No supported firewall (ufw/iptables) found.")
        return None

    def block_ip(self, ip: str) -> bool:
        if self.dry_run:
            logger.info(f"[DRY RUN] Would block IP: {ip}")
            return True

        try:
            if self.firewall_type == 'ufw':
                return self._block_with_ufw(ip)
            elif self.firewall_type == 'iptables':
                return self._block_with_iptables(ip)
        except Exception as e:
            logger.error(f"Error blocking {ip}: {e}")
        return False

    def _block_with_ufw(self, ip: str) -> bool:
        result = subprocess.run(['ufw', 'deny', 'from', ip, 'to', 'any'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0

    def _block_with_iptables(self, ip: str) -> bool:
        if os.system(f"iptables -C INPUT -s {ip} -j DROP 2>/dev/null") == 0:
            logger.info(f"IP already blocked: {ip}")
            return True

        result = subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0


# -------------------- Main Utilities -------------------- #
def check_root() -> bool:
    """Ensure the script is run as root."""
    if os.geteuid() != 0:
        logger.error("Script must be run as root (sudo).")
        return False
    return True

def parse_arguments():
    parser = argparse.ArgumentParser(description="SSH Brute Force Protection Script")
    parser.add_argument('--threshold', type=int, default=5)
    parser.add_argument('--interval', type=int, default=60)
    parser.add_argument('--whitelist', nargs='+', default=[])
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    return parser.parse_args()

def handle_signals(signum, frame):
    logger.info("Termination signal received. Cleaning up...")
    log_monitor.stop()
    sys.exit(0)

# -------------------- Main Entry -------------------- #
if __name__ == "__main__":
    args = parse_arguments()
    logger.setLevel(getattr(logging, args.log_level))

    if not check_root():
        sys.exit(1)

    # Signal handling
    signal.signal(signal.SIGINT, handle_signals)
    signal.signal(signal.SIGTERM, handle_signals)

    # Set up and run
    threat_detector = ThreatDetector(args.threshold, args.interval, args.whitelist)
    firewall_manager = FirewallManager(dry_run=args.dry_run)
    threat_detector.set_firewall_manager(firewall_manager)

    log_monitor = LogMonitor(threat_detector)

    logger.info(f"Running with threshold={args.threshold}, interval={args.interval}s")
    if args.whitelist:
        logger.info(f"Whitelisted IPs: {', '.join(args.whitelist)}")
    if args.dry_run:
        logger.info("DRY RUN mode enabled - no IPs will be blocked")

    log_monitor.start()

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_monitor.stop()
        logger.info("Stopped SSH brute force protection.")
