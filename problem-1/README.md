# 🛒 E-commerce Price Spy

A smart Python script that automates price tracking across multiple e-commerce websites. Perfect for deal hunters who want to monitor product prices without manual checking.

## 🌟 Features

- **Dual scraping system**: Uses both BeautifulSoup (fast) and Selenium (for JS-rendered pages)
- **Wide compatibility**: Works with Amazon, Meesho, BooksToScrape, and more
- **Smart detection**: Handles 10+ different price formats and HTML structures
- **Error resilient**: Automatic fallback mechanisms and robust exception handling

## 📦 Setup

### Prerequisites
- Python 3.8+
- Chrome browser installed
- ChromeDriver (auto-installed by webdriver-manager)

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/price-spy.git
cd price-spy

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt