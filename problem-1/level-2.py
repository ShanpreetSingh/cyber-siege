"""
🕵️‍♂️ Dynamic Pricing Tracker
---------------------------
Tracks price fluctuations across e-commerce platforms and analyzes pricing strategies.
Generates detailed CSV reports with price history and detects significant changes.
"""

# === Imports ===

import requests  # For making HTTP requests to the API
import csv       # For writing data to CSV files
import time      # For handling time-based operations
from datetime import datetime  # For timestamping
import json      # For handling JSON data
from typing import List, Dict  # For type hinting
import os        # For working with file paths


# === Price Tracker Class ===

class PriceTracker:
    def __init__(self, api_base_url: str = "https://cyber.istenith.com"):
        """
        Initialize the price tracker with API configuration

        Args:
            api_base_url: Base URL of the mock API to fetch product data
        """
        self.api_base_url = api_base_url
        self.price_history = {}  # Stores price data per product: {product_id: [{timestamp, price}]}
        self.alert_threshold = 0.05  # Threshold for alerting price changes (5%)

    def fetch_product_list(self) -> List[Dict]:
        """
        Fetch the list of all products from the API

        Returns:
            A list of products (each as a dictionary)
        """
        try:
            response = requests.get(f"{self.api_base_url}/products", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"⚠️ Failed to fetch products: {e}")
            return []

    def get_current_price(self, product_id: str) -> float:
        """
        Get the current price of a product by its ID

        Args:
            product_id: The unique product identifier

        Returns:
            The price as a float, or None on failure
        """
        try:
            response = requests.get(f"{self.api_base_url}/products/{product_id}/price", timeout=10)
            response.raise_for_status()
            return float(response.json()['price'])
        except (requests.RequestException, KeyError, ValueError) as e:
            print(f"⚠️ Error getting price for {product_id}: {e}")
            return None

    def track_prices(self, interval_minutes: int = 30, duration_hours: int = 24):
        """
        Continuously track prices over a given time period

        Args:
            interval_minutes: Time between each check in minutes
            duration_hours: Total duration to track prices in hours
        """
        products = self.fetch_product_list()
        if not products:
            print("❌ No products found to track")
            return

        print(f"🔍 Starting to track {len(products)} products...")
        end_time = time.time() + duration_hours * 3600  # Calculate end time

        # Main tracking loop
        while time.time() < end_time:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n🕒 Checking prices at {current_time}")

            for product in products:
                product_id = product['id']
                product_name = product['name']
                current_price = self.get_current_price(product_id)

                if current_price is None:
                    continue  # Skip if price couldn't be fetched

                self._update_price_history(product_id, product_name, current_price)
                self._check_for_price_changes(product_id, current_price)

            # Save data after every interval
            self.export_to_csv()
            print(f"💾 Data saved. Next check in {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)

    def _update_price_history(self, product_id: str, product_name: str, price: float):
        """
        Store the price data with a timestamp for a product

        Args:
            product_id: ID of the product
            product_name: Name of the product
            price: Current price to record
        """
        timestamp = datetime.now().isoformat()

        # Initialize entry if it doesn't exist
        if product_id not in self.price_history:
            self.price_history[product_id] = {
                'name': product_name,
                'history': []
            }

        history = self.price_history[product_id]['history']

        # Record only if price changed or it's the first entry
        if not history or history[-1]['price'] != price:
            history.append({
                'timestamp': timestamp,
                'price': price
            })

    def _check_for_price_changes(self, product_id: str, current_price: float):
        """
        Check if the product price changed significantly (based on threshold)

        Args:
            product_id: ID of the product
            current_price: Current price to compare
        """
        history = self.price_history[product_id]['history']
        if len(history) < 2:
            return  # Not enough data to compare

        previous_price = history[-2]['price']
        price_change = (current_price - previous_price) / previous_price

        if abs(price_change) >= self.alert_threshold:
            product_name = self.price_history[product_id]['name']
            direction = "↑" if price_change > 0 else "↓"
            print(f"🚨 ALERT: {product_name} changed by {abs(price_change):.1%} {direction}")

    def export_to_csv(self, filename: str = "price_history.csv"):
        """
        Save all price history data to a CSV file

        Args:
            filename: Name of the file to save to
        """
        try:
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['product_id', 'product_name', 'timestamp', 'price']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                # Write data for each product and time entry
                for product_id, data in self.price_history.items():
                    for entry in data['history']:
                        writer.writerow({
                            'product_id': product_id,
                            'product_name': data['name'],
                            'timestamp': entry['timestamp'],
                            'price': entry['price']
                        })

            print(f"📊 Data exported to {filename}")
        except IOError as e:
            print(f"⚠️ Failed to export data: {e}")

    def analyze_data(self, filename: str = "price_history.csv"):
        """
        Analyze price history data to show overall trend

        Args:
            filename: CSV file containing the data (optional)
        """
        print("\n📈 Price Analysis Summary:")
        for product_id, data in self.price_history.items():
            prices = [entry['price'] for entry in data['history']]
            if len(prices) > 1:
                change = (prices[-1] - prices[0]) / prices[0]
                print(f"{data['name']}: {change:+.1%} change over tracking period")


# === Script Entry Point ===

if __name__ == "__main__":
    print("""
    🌐 Dynamic Pricing Tracker
    --------------------------
    This tool will:
    1. Track product prices from the mock API
    2. Detect significant price changes (>5%)
    3. Save complete history to CSV
    4. Run for 24 hours (configurable)
    """)

    # Create the tracker and run it for 24 hours, checking every 30 minutes
    tracker = PriceTracker()
    tracker.track_prices(
        interval_minutes=30,  # Check every 30 minutes
        duration_hours=24     # Run for 24 hours
    )
    
    # After tracking ends, generate a summary and export final CSV
    tracker.analyze_data()
    tracker.export_to_csv()
