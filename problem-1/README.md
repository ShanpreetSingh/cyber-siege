# 🛒 Dynamic & Stealth Price Trackers

A multi-level project for tracking product prices from e-commerce websites. This repository contains **three progressive implementations**—from basic API usage to full stealth scraping bypassing CAPTCHAs and bot detection systems.

---

## 📦 Levels Overview

### 🔹 Level 1: Basic Web Scraper (Static or Public API)
> **File:** `level1_basic_scraper.py`

- Tracks product prices from a static or mock API.
- Detects significant price changes (±5%) and logs them.
- Saves price history to CSV.
- Ideal for learning and simple use cases.

---

### 🔷 Level 2: API Price Tracker (Dynamic Tracking)
> **File:** `level2_api_tracker.py`

- Continuously polls product price data from a mock REST API.
- Tracks price history with timestamps.
- Alerts on significant fluctuations (default: 5%).
- Exports detailed CSV reports.
- Includes an analysis summary to show trends over time.

---

### 🕵️‍♂️ Level 3: Ghost Price Tracker (Stealth Scraper)
> **File:** `level3_ghost_tracker.py`

- Uses `undetected_chromedriver` with random user-agents and stealth options.
- Mimics human behavior with random delays and cursor movement.
- Solves CAPTCHA manually (semi-automated fallback).
- Logs real-time price changes and exports CSV history.

---

## ⚙️ Setup Instructions
Absolutely! Here's a comprehensive and clean **Setup Guide** you can paste directly into your README after the levels section. This will walk users through installing dependencies and running the scripts.

---
### 🐍 Requirements

Install dependencies (common for all levels):
requests==2.31.0              # For API requests (Level 1 & 2)
undetected-chromedriver==3.5.5  # For stealth browser automation (Level 3)
selenium==4.19.0              # Required for interacting with web pages (Level 3)
fake-useragent==1.5.1         # Generates random user agents to mimic browsers (Level 3)



## ⚙️ Setup Instructions

Follow the steps below to set up and run the price tracking tools on your machine.

---

### 🐍 1. Install Python

Make sure Python **3.8+** is installed.

- Download from [python.org](https://www.python.org/downloads/)
- Verify installation:
  ```bash
  python --version
  ```

---

### 📁 2. Clone the Repository

```bash
git clone https://github.com/yourusername/price-trackers.git
cd price-trackers
```

---

### 📦 3. Create Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
```

---

### 📥 4. Install Dependencies

Install all required packages for all three levels:

```bash
pip install -r requirements.txt
```

#### 🧩 `requirements.txt` contains:

| Package                    | Purpose                                       |
|---------------------------|-----------------------------------------------|
| `requests`                | Used in Level 1 & 2 to fetch data from APIs   |
| `undetected-chromedriver`| Enables stealth browser scraping in Level 3   |
| `selenium`                | Automates browser interaction for scraping    |
| `fake-useragent`          | Randomizes browser user-agent strings         |

---

### 🛠️ 5. Run the Trackers

You can run each tracker directly from the command line:

#### 🔹 Level 1: Basic Scraper

```bash
python level1_basic_scraper.py
```

#### 🔷 Level 2: API Price Tracker

```bash
python level2_api_tracker.py
```

#### 🕵️‍♂️ Level 3: Ghost Price Tracker

```bash
python level3_ghost_tracker.py
```

> 🧠 **Note:** Level 3 will open a browser window. You may need to manually solve CAPTCHAs if they appear.

---

### 📊 6. Output Files

- All levels generate a CSV file:
  - `price_history.csv` — contains product price history over time.
- Level 2 also prints an analysis summary of price trends after tracking ends.

---

### 🧽 7. Cleanup

When done, you can deactivate the virtual environment:

```bash
deactivate
'''

---


