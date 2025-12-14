# Web Scraper Synthesis Demo

## Overview
This demo shows how to synthesize a complete web scraping project using the AI Project Synthesizer.

## MCP Server Command

```
Synthesize a project from the idea: "Create a web scraper using BeautifulSoup and requests that can extract data from e-commerce websites including product names, prices, and ratings"
```

## Expected Result

The AI Project Synthesizer will:

1. **Search for Relevant Repositories**
   - Find BeautifulSoup scraping examples
   - Locate requests-based scrapers
   - Discover data processing utilities

2. **Create Project Structure**
   ```
   web-scraper-project/
   ├── src/
   │   ├── scraper/
   │   │   ├── __init__.py
   │   │   ├── base_scraper.py
   │   │   ├── ecommerce_scraper.py
   │   │   └── utils.py
   │   └── data/
   │       ├── __init__.py
   │       ├── processor.py
   │       └── exporter.py
   ├── tests/
   │   ├── test_scraper.py
   │   └── test_data_processor.py
   ├── config/
   │   ├── settings.yaml
   │   └── user_agents.txt
   ├── requirements.txt
   ├── README.md
   └── .gitignore
   ```

3. **Generate Requirements**
   ```txt
   # Core dependencies
   torch>=2.0.0
   transformers>=4.30.0
   datasets>=2.0.0
   numpy>=1.24.0
   pandas>=2.0.0
   
   # Utilities
   tqdm
   python-dotenv
   pyyaml
   
   # Web scraping
   requests>=2.31.0
   beautifulsoup4>=4.12.0
   lxml>=4.9.0
   selenium>=4.15.0
   ```

4. **Create README with Usage Instructions**

## Usage Example

After synthesis, you can use the scraper:

```python
from src.scraper.ecommerce_scraper import EcommerceScraper

scraper = EcommerceScraper()
products = scraper.scrape_products("https://example-store.com/category")

for product in products:
    print(f"Name: {product['name']}")
    print(f"Price: {product['price']}")
    print(f"Rating: {product['rating']}")
```

## Features Included

- Product data extraction
- Price parsing and currency conversion
- Rating aggregation
- Export to CSV/JSON
- Rate limiting and respectful scraping
- Error handling and retries
- Proxy support
- Headless browser option

## Customization

The synthesized project includes:
- Configurable selectors in `config/settings.yaml`
- Custom user agents in `config/user_agents.txt`
- Extensible base scraper class
- Modular data processing pipeline

## Next Steps

1. Run the project: `pip install -r requirements.txt`
2. Configure settings for your target sites
3. Customize the scraper classes as needed
4. Add your own data processing logic
5. Deploy using the included Dockerfile (if generated)
