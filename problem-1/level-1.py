# === Imports ===

# Standard libraries
import requests  # For sending HTTP requests
from bs4 import BeautifulSoup  # For parsing HTML content
import re  # Regular expressions for text processing
import argparse  # For command-line argument parsing
import time  # For adding delays
import logging  # For logging activity (info, warnings, errors)
from urllib.parse import urlparse  # For extracting domain from URL

# Selenium libraries for browser automation
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

# To automatically manage ChromeDriver installation
from webdriver_manager.chrome import ChromeDriverManager


# === Logging Setup ===

# Configure logging to both a log file and the console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("price_tracker.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# === Price Tracker Class ===

class PriceTracker:

    def __init__(self, headless=True):
        """
        Initialize the tracker with optional headless browser mode
        and a persistent requests session.
        """
        self.headless = headless  # Run browser in background if True
        self.driver = None
        self.session = requests.Session()

        # Set a user-agent header to avoid being blocked by websites
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        })

    def _setup_driver(self):
        """
        Configure and return a Selenium Chrome WebDriver instance.
        """
        try:
            options = Options()

            if self.headless:
                options.add_argument("--headless")  # Run without opening a window

            # Additional browser options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 ... Safari/537.36")

            # Auto-install and launch ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)  # Set page load timeout

            return driver

        except WebDriverException as e:
            logger.error(f"WebDriver setup failed: {e}")
            raise

    def close(self):
        """
        Close the browser if it was opened.
        """
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing driver: {e}")

    def _clean_price(self, text):
        """
        Convert raw price text to a float value.
        Removes currency symbols, commas, etc.
        """
        if not text:
            return None

        cleaned = re.sub(r'[^\d.,]', '', text)  # Remove non-numeric characters
        cleaned = cleaned.replace(',', '')

        try:
            return float(cleaned)
        except ValueError:
            logger.warning(f"Could not convert price: {text}")
            return None

    def _get_with_requests(self, url):
        """
        Try to fetch page content using the requests module.
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            logger.error(f"Requests failed: {e}")
            return None

    def _get_with_selenium(self, url):
        """
        Fetch page using a headless browser (Selenium).
        Useful for JavaScript-heavy websites.
        """
        if not self.driver:
            self.driver = self._setup_driver()

        try:
            self.driver.get(url)

            # Wait until at least the <body> tag is loaded
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            time.sleep(5)  # Wait for dynamic content to load

            return BeautifulSoup(self.driver.page_source, 'html.parser')

        except Exception as e:
            logger.error(f"Selenium failed: {e}")
            return None

    def get_domain(self, url):
        """
        Extract the domain name from a given URL.
        """
        return urlparse(url).netloc

    # === Site-Specific Extraction Methods ===

    def extract_books_toscrape(self, soup):
        """
        Extract product name and price from books.toscrape.com
        """
        try:
            name = soup.select_one('.product_main h1').text.strip()
            price_text = soup.select_one('.price_color').text.strip()
            return name, self._clean_price(price_text), price_text
        except Exception as e:
            logger.error(f"BooksToScrape extract failed: {e}")
            return None, None, None

    def extract_meesho(self, soup):
        """
        Extract product name and price from meesho.com
        """
        try:
            name = soup.select_one('h1').text.strip()
            price_el = soup.select_one('[class*="price"]') or soup.select_one('[class*="Price"]')
            price_text = price_el.text.strip() if price_el else None
            return name, self._clean_price(price_text), price_text
        except Exception as e:
            logger.error(f"Meesho extract failed: {e}")
            return None, None, None

    def extract_amazon(self, soup):
        """
        Extract product name and price from amazon.com
        """
        try:
            name = soup.select_one('#productTitle').text.strip()

            selectors = [
                '.a-price .a-offscreen',
                '#priceblock_ourprice',
                '#priceblock_dealprice',
                '.a-size-large.a-color-price',
                '[data-a-color="price"] .a-offscreen'
            ]

            price_text = next(
                (soup.select_one(sel).text.strip() for sel in selectors if soup.select_one(sel)),
                None
            )

            return name, self._clean_price(price_text), price_text
        except Exception as e:
            logger.error(f"Amazon extract failed: {e}")
            return None, None, None

    def extract_flipkart(self, soup):
        """
        Extract product name and price from flipkart.com
        """
        try:
            name_el = soup.select_one('span.B_NuCI')
            price_el = soup.select_one('div._30jeq3._16Jk6d')

            # Fallback selectors for different layouts
            if not name_el or not price_el:
                product = soup.select_one('div._1AtVbE')
                if product:
                    name_el = product.select_one('div._4rR01T')
                    price_el = product.select_one('div._30jeq3._1_WHN1')

            if not name_el or not price_el:
                return None, None, None

            name = name_el.text.strip()
            price_text = price_el.text.strip()

            return name, self._clean_price(price_text), price_text
        except Exception as e:
            logger.error(f"Flipkart extract failed: {e}")
            return None, None, None

    def extract_generic(self, soup):
        """
        Try to extract name and price using common HTML patterns.
        Works for unknown or unsupported websites.
        """
        try:
            # Try common selectors for product name
            name = None
            for sel in ['h1', '.product-title', '.product-name', '[class*="product"][class*="title"]']:
                el = soup.select_one(sel)
                if el:
                    name = el.text.strip()
                    break

            # Try to find price using various patterns
            price_text = None
            for sel in [
                '[class*="price"]', '[id*="price"]', '.price', '[class*="Price"]',
                '[data-price]', '[class*="product-price"]'
            ]:
                elements = soup.select(sel)
                for el in elements:
                    text = el.text.strip()
                    if re.search(r'\d+([.,]\d+)?', text):
                        price_text = text
                        break
                if price_text:
                    break

            # Last resort: regex search in raw text
            if not price_text:
                match = re.search(r'(?:price|cost|amount)[^\d]*([\d.,]+)', soup.text, re.IGNORECASE)
                price_text = match.group(1) if match else None

            return name, self._clean_price(price_text), price_text
        except Exception as e:
            logger.error(f"Generic extract failed: {e}")
            return None, None, None

    def _extract_currency(self, price_text):
        """
        Try to identify currency based on symbols in price text.
        """
        if not price_text:
            return None

        symbols = {
            '₹': 'INR', '$': 'USD', '€': 'EUR', '£': 'GBP',
            '¥': 'JPY', '₩': 'KRW', '₽': 'RUB', 'Rs': 'INR',
            'Rs.': 'INR', 'rupees': 'INR'
        }

        for sym, code in symbols.items():
            if sym in price_text:
                return code

        return 'INR'  # Default to INR

    def get_price(self, url):
        """
        Master method to determine which extractor to use
        and return the product details.
        """
        domain = self.get_domain(url)
        logger.info(f"Fetching from: {domain}")

        soup = None

        # Some sites need Selenium for JS rendering
        if 'flipkart.com' in domain:
            soup = self._get_with_selenium(url)
            time.sleep(5)
        else:
            soup = self._get_with_requests(url)

            # Fallback to Selenium for complex pages
            if not soup and any(site in domain for site in ['meesho.com', 'amazon']):
                soup = self._get_with_selenium(url)

        if not soup:
            return {'success': False, 'error': 'Page fetch failed', 'url': url}

        # Select appropriate extractor based on site
        if 'books.toscrape.com' in domain:
            name, price, price_text = self.extract_books_toscrape(soup)
        elif 'meesho.com' in domain:
            name, price, price_text = self.extract_meesho(soup)
        elif 'amazon' in domain:
            name, price, price_text = self.extract_amazon(soup)
        elif 'flipkart.com' in domain:
            name, price, price_text = self.extract_flipkart(soup)
        else:
            name, price, price_text = self.extract_generic(soup)

        # Fallback if site-specific extract failed
        if not name or not price:
            logger.info("Trying generic extractor as fallback...")
            name, price, price_text = self.extract_generic(soup)

        if not name or not price:
            return {'success': False, 'error': 'Extraction failed', 'url': url}

        return {
            'success': True,
            'product_name': name,
            'price': price,
            'price_text': price_text,
            'currency': self._extract_currency(price_text),
            'url': url
        }


# === CLI Entrypoint ===

def main():
    """
    Command-line interface: takes URL input and prints result.
    """
    parser = argparse.ArgumentParser(description='Track product price from URL')
    parser.add_argument('--url', type=str, help='Product URL')
    parser.add_argument('--no-headless', action='store_true', help='Run browser with GUI')
    args = parser.parse_args()

    url = args.url or input("Enter product URL: ")
    tracker = PriceTracker(headless=not args.no_headless)

    try:
        result = tracker.get_price(url)

        if result['success']:
            print("\n=== Product Info ===")
            print(f"Name         : {result['product_name']}")
            print(f"Price        : {result['price_text']} ({result['currency']})")
            print(f"Numeric Price: {result['price']}")
            print(f"URL          : {result['url']}")
        else:
            print(f"Error: {result['error']}")

    except KeyboardInterrupt:
        print("\nCancelled by user")

    except Exception as e:
        print(f"Unexpected error: {e}")

    finally:
        tracker.close()


# === Run Script ===

if __name__ == "__main__":
    main()
