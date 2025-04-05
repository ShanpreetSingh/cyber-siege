"""
🛒 E-commerce Price Spy
-----------------------
Automatically extracts product names and prices from various e-commerce sites.
Handles both static and JavaScript-rendered pages with smart fallback logic.
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
from selenium.common.exceptions import WebDriverException

class PriceSpy:
    def __init__(self):
        """Initialize with browser options"""
        self.setup_browser()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })

    def setup_browser(self):
        """Configure Chrome options for Selenium"""
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option("useAutomationExtension", False)
        self.browser = None

    def get_product_info(self, url):
        """
        Main function to get product info
        Returns: {'name': str, 'price': str, 'store': str, 'status': 'success'/'failed'}
        """
        result = {
            'url': url,
            'name': None,
            'price': None,
            'store': urlparse(url).netloc,
            'status': 'success'
        }

        try:
            # First try with fast requests method
            soup = self.try_requests(url)
            
            # If price not found, try Selenium
            if not self.find_price(soup):
                soup = self.try_selenium(url)
            
            if soup:
                result['name'] = self.find_product_name(soup)
                result['price'] = self.find_price(soup) or "Price not found"
            else:
                result['status'] = 'failed'
                result['price'] = "Failed to load page"

        except Exception as e:
            result['status'] = 'failed'
            result['price'] = f"Error: {str(e)[:100]}"

        return result

    def try_requests(self, url):
        """Try fast requests method first"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except:
            return None

    def try_selenium(self, url):
        """Fallback to Selenium for JS pages"""
        try:
            if not self.browser:
                self.browser = webdriver.Chrome(options=self.chrome_options)
            
            self.browser.get(url)
            time.sleep(3)  # Wait for JS rendering
            return BeautifulSoup(self.browser.page_source, 'html.parser')
        except WebDriverException as e:
            print(f"Selenium Error: {str(e)[:200]}")
            return None

    def find_price(self, soup):
        """Find price using multiple strategies"""
        price_selectors = [
            '.price', '.product-price', '#priceblock_ourprice',
            '.a-price-whole', '.a-offscreen', '[itemprop="price"]',
            '.final-price', '.amount', '.selling-price'
        ]
        
        price_patterns = [
            r'₹\s?\d+[,.]?\d+',  # Indian rupees
            r'\$\d+[,.]?\d+',     # US dollars
            r'\d+[,.]?\d+\s?[A-Z]{3}'  # 100.00 USD
        ]

        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                for pattern in price_patterns:
                    if re.search(pattern, price_text):
                        return price_text
        return None

    def find_product_name(self, soup):
        """Extract product name"""
        name_selectors = [
            'h1', '.product-title', '#productTitle',
            '.name', '.title', '[itemprop="name"]'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()[:100]  # Limit name length
        return "Unknown Product"

    def close(self):
        """Clean up resources"""
        if self.browser:
            self.browser.quit()

# Test the scraper
if __name__ == "__main__":
    spy = PriceSpy()
    
    test_urls = [
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "https://books.toscrape.com/catalogue/silence-in-the-dark-logan-point-4_542/index.html",
        "https://www.meesho.com/imported-popcorn-stylish-shirts-for-mens-and-female/p/67avhd",
        "https://www.amazon.in/Praylady-TRIPLUS-Triple-Layered-Stainless-Steel-Aluminum/dp/B0DZH4RGJX/ref=sr_1_1_sspa?crid=T5AWS0NS2QEI&dib=eyJ2IjoiMSJ9.Lpn3iPNPcMlm7HNRgApQwedGGpnrYEpguZFCss3aiaiVejy6Xdi7-Y2yYzH0xBxaDfTmZk479xcFu33I7wt626IUUOM-hLwncUyzNwolD_1aoFEHoAikKMSU3rGpYi7SubeIrOpkTAaWsuxrLpJmQq95wxNMSoZPuBaPVws6X1Hz-h-7vyXVNiy-b_PsZcCfi1Nm-C1x6wIMYlT6vBYPSFBk79GMXlAkDe2u6EF6_h7Sr4T_Y8vYmrd16Wb6Xcs10pfk76N6q46pMPNmh9ZT5CuR2cVfu4l_qghxHk8OpNE.LdQPn4tFsrziZyQzqc5RDirxrgiTIkXn6CH0d_SIEUg&dib_tag=se&keywords=cooking%2Bset&qid=1743800141&sprefix=cooking%2Bset%2Caps%2C311&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1",
        "https://www.flipkart.com/tyy/4io/~cs-mym7b91vfx/pr?sid=tyy%2C4io&collection-tab-name=POCO+X7+5G&pageCriteria=default&param=34232&hpid=pGWhZceh7U77ikpg0pfIJap7_Hsxr70nj65vMAAFKlc%3D&ctx=eyJjYXJkQ29udGV4dCI6eyJhdHRyaWJ1dGVzIjp7InZhbHVlQ2FsbG91dCI6eyJtdWx0aVZhbHVlZEF0dHJpYnV0ZSI6eyJrZXkiOiJ2YWx1ZUNhbGxvdXQiLCJpbmZlcmVuY2VUeXBlIjoiVkFMVUVfQ0FMTE9VVCIsInZhbHVlcyI6WyJKdXN0IOKCuTE3LDk5OSoiXSwidmFsdWVUeXBlIjoiTVVMVElfVkFMVUVEIn19LCJoZXJvUGlkIjp7InNpbmdsZVZhbHVlQXR0cmlidXRlIjp7ImtleSI6Imhlcm9QaWQiLCJpbmZlcmVuY2VUeXBlIjoiUElEIiwidmFsdWUiOiJNT0JIN1laOURISFNNR0hOIiwidmFsdWVUeXBlIjoiU0lOR0xFX1ZBTFVFRCJ9fSwidGl0bGUiOnsibXVsdGlWYWx1ZWRBdHRyaWJ1dGUiOnsia2V5IjoidGl0bGUiLCJpbmZlcmVuY2VUeXBlIjoiVElUTEUiLCJ2YWx1ZXMiOlsiUG9jbyBYNyA1RyJdLCJ2YWx1ZVR5cGUiOiJNVUxUSV9WQUxVRUQifX19fX0%3D"
    ]
    
    print("🛍️ Starting Price Spy Scraper...\n")
    
    for url in test_urls:
        print(f"🔍 Checking: {url}")
        result = spy.get_product_info(url)
        
        if result['status'] == 'success':
            print(f"✅ Product: {result['name']}")
            print(f"💰 Price: {result['price']}")
            print(f"🏪 Store: {result['store']}\n")
        else:
            print(f"❌ Failed to check: {result['price']}\n")
    
    spy.close()
    print("✨ Price check complete!")