# 🔐 SSH Brute Force Protection Script

A Python-based Linux utility to **monitor SSH login attempts** and automatically **block IPs** exhibiting brute-force behavior using `iptables` or `ufw`.

---

## ⚙️ Features

- ✅ Real-time monitoring of SSH login failures
- ✅ Supports both `/var/log/auth.log` and `journalctl`
- ✅ IP blocking via `ufw` or `iptables`
- ✅ Whitelist trusted IPs
- ✅ Adjustable thresholds and time intervals
- ✅ Dry-run mode for testing
- ✅ Logs all activity with timestamps

---

## 📦 Dependencies

### Python
This script uses only standard libraries, so no pip installation is needed.

### System (Linux only)
- SSH daemon (`sshd`)
- Either:
  - `/var/log/auth.log` (Debian/Ubuntu), or
  - `journalctl` (systemd-based systems)
- One firewall utility:
  - `ufw`, or
  - `iptables`
- Must be run with **sudo/root** privileges.

---

## 🚀 Installation & Usage

### 1. Clone the repository:
```bash
git clone https://github.com/your-username/ssh-brute-force-blocker.git
cd ssh-brute-force-blocker
