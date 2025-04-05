"""
🕵️‍♂️ Ghost Price Tracker
-----------------------
A stealthy web scraper that bypasses CAPTCHAs and anti-bot systems to track e-commerce prices.
Uses undetected ChromeDriver, human-like behavior patterns, and automatic retries.
"""

# === Imports ===
import time
import random
import csv
from datetime import datetime
from urllib.parse import urlparse

# Stealth browser & scraping tools
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent  # Generates random user-agents to mimic human browsers

# === Ghost Tracker Class ===

class StealthPriceTracker:
    def __init__(self):
        self.driver = None
        self.price_history = {}  # Stores price history data for each product
        self.ua = UserAgent()    # Generates random user-agents
        self.retry_limit = 3     # Max number of retries for scraping a product
        self.human_delays = (2, 5)  # Delay range to mimic human browsing behavior
        self.setup_driver()

    def setup_driver(self):
        """Set up an undetectable ChromeDriver with anti-bot bypassing settings"""
        options = uc.ChromeOptions()

        # Spoofing settings to reduce detection chances
        options.add_argument(f"user-agent={self.ua.random}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        self.driver = uc.Chrome(
            options=options,
            headless=False  # Set to True for invisible operation
        )

        try:
            # Hide Selenium from detection
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
        except:
            pass

    def human_delay(self):
        """Sleep for a random duration to simulate human-like delays"""
        time.sleep(random.uniform(*self.human_delays))

    def solve_captcha(self):
        """Detect CAPTCHA presence and prompt for manual solving"""
        try:
            if "captcha" in self.driver.page_source.lower():
                print("⚠️ CAPTCHA detected - please solve manually in browser")
                for _ in range(60):  # Wait up to 60 seconds for manual solve
                    if "captcha" not in self.driver.page_source.lower():
                        return True
                    time.sleep(1)
                return False
            self.driver.quit()
            self.setup_driver()
            return True
        except Exception as e:
            print(f"CAPTCHA handling error: {str(e)[:100]}")
            return False

    def scrape_walmart(self, product_url):
        """Scrape product name and price from a Walmart product page"""
        for attempt in range(self.retry_limit):
            try:
                self.driver.get(product_url)
                self.human_delay()

                # Wait for price element to appear
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='price']"))
                )

                # Scroll to trigger lazy loading
                self.driver.execute_script("window.scrollBy(0, window.innerHeight/3)")
                self.human_delay()

                # Extract price and product name
                price_el = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='price']")
                price = float(price_el.text.replace('$', '').replace(',', ''))

                name_el = self.driver.find_element(By.CSS_SELECTOR, "h1.prod-ProductTitle")
                name = name_el.text.strip()

                return name, price

            except Exception as e:
                print(f"Attempt {attempt+1} failed: {str(e)[:100]}")
                if not self.solve_captcha():
                    break
                self.human_delay()

        return None, None

    def scrape_bestbuy(self, product_url):
        """Scrape product name and price from a BestBuy product page"""
        for attempt in range(self.retry_limit):
            try:
                self.driver.get(product_url)
                self.human_delay()

                # Move mouse slightly to simulate real activity
                self.driver.execute_script("""
                    window.moveBy(
                        Math.random() * 100, 
                        Math.random() * 100
                    )""")

                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "priceView-customer-price"))
                )

                price_el = self.driver.find_element(By.CLASS_NAME, "priceView-customer-price")
                price = float(price_el.text.split('$')[-1].replace(',', ''))

                name_el = self.driver.find_element(By.CSS_SELECTOR, "h1.heading-5")
                name = name_el.text.strip()

                return name, price

            except Exception as e:
                print(f"Attempt {attempt+1} failed: {str(e)[:100]}")
                if not self.solve_captcha():
                    break
                self.human_delay()

        return None, None

    def track_product(self, url, interval_min=30, duration_hrs=24):
        """
        Track a product's price over time

        Args:
            url: Product page URL
            interval_min: Interval in minutes between each check
            duration_hrs: Total tracking time in hours
        """
        domain = urlparse(url).netloc
        product_id = url.split('/')[-1]  # Basic ID using last URL segment

        # Set up history container
        if product_id not in self.price_history:
            self.price_history[product_id] = {
                'name': '',
                'domain': domain,
                'history': []
            }

        end_time = time.time() + duration_hrs * 3600

        while time.time() < end_time:
            try:
                # Select appropriate scraper based on domain
                if 'walmart.com' in domain:
                    name, price = self.scrape_walmart(url)
                elif 'bestbuy.com' in domain:
                    name, price = self.scrape_bestbuy(url)
                else:
                    raise ValueError("Unsupported website")

                # Log price if successful
                if price:
                    timestamp = datetime.now().isoformat()
                    if name:
                        self.price_history[product_id]['name'] = name

                    self.price_history[product_id]['history'].append({
                        'timestamp': timestamp,
                        'price': price
                    })

                    print(f"✅ {domain} | {name}: ${price:.2f} at {timestamp}")
                    self.detect_price_changes(product_id, price)

                # Save to file and wait for next check
                self.export_to_csv()
                time.sleep(interval_min * 60)

            except Exception as e:
                print(f"Critical error: {str(e)[:100]}")
                time.sleep(60)

    def detect_price_changes(self, product_id, current_price):
        """Detect price fluctuation exceeding 5% from previous recorded price"""
        history = self.price_history[product_id]['history']
        if len(history) > 1:
            prev_price = history[-2]['price']
            change = (current_price - prev_price) / prev_price
            if abs(change) >= 0.05:
                direction = "↑" if change > 0 else "↓"
                print(f"🚨 PRICE ALERT: {abs(change):.1%} change {direction}")

    def export_to_csv(self, filename="price_history.csv"):
        """Save current price history data to a CSV file"""
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Product ID', 'Name', 'Domain', 'Timestamp', 'Price'])

                for product_id, data in self.price_history.items():
                    for entry in data['history']:
                        writer.writerow([
                            product_id,
                            data['name'],
                            data['domain'],
                            entry['timestamp'],
                            entry['price']
                        ])
            print(f"💾 Data saved to {filename}")
        except Exception as e:
            print(f"Failed to export data: {str(e)[:100]}")

    def close(self):
        """Close the browser driver cleanly"""
        if self.driver:
            self.driver.quit()


# === Script Execution ===

if __name__ == "__main__":
    tracker = StealthPriceTracker()

    # List of product URLs to track (can be expanded)
    products = [
        "https://www.walmart.com/ip/Sony-PlayStation-5-Digital-Edition/493824815",
        "https://www.bestbuy.com/site/sony-playstation-5-digital-edition-console/6430161.p"
    ]

    try:
        # Start tracking each product for 30 minutes with 5-min intervals
        for url in products:
            print(f"\n🔍 Starting tracking for {url}")
            tracker.track_product(url, interval_min=5, duration_hrs=0.5)
    finally:
        tracker.close()
