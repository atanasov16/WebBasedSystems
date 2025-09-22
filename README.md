<img width="1919" height="904" alt="jsonldToReforgedData" src="https://github.com/user-attachments/assets/d120fc1e-38ca-43c0-86c5-ff7ce21fbbde" />Tech Price Scraper & Semantic Data Refactor

This system automatically scrapes product data (Laptops, TVs, and Smartphones) from leading North Macedonian retailers and transforms it into a standardized, semantic JSON-LD format using Schema.org
 vocabulary.

The result is not just a dataset but a semantic knowledge graph snippet – ready to be consumed by search engines, comparison apps, or graph databases.

1. Project Structure
   
data/                   # Raw scraped data (CSV files)

reforged_data/          # Processed semantic data (JSON-LD files)

scrapers/               # Web scraper scripts

utils/                  # Data processing utilities

3. Features

- Multi-Source Data Acquisition – Scrapes products from Anhoch, Neptun, Setec & Tehnomarket.

- Structured Data Parsing – Extracts product name, price, brand, model, and specs.

- Semantic Enrichment – Converts raw data to JSON-LD (Schema.org) with Product & Offer.

- Category-Specific Processing – Custom parsing for Laptops, Smartphones, and Televisions.

- Robust Scraping – Selenium handles JavaScript-rendered content & lazy loading.

- Two-Phase Design – Separation of scraping (volatile) and data modeling (stable).

3. Tech used
Selenium - Dynamic web scraping	Required due to JS-heavy sites
BeautifulSoup4 - HTML parsing	Simple API for navigating HTML
Pandas -	Data manipulation + CSV I/O	Makes handling tabular data easy
JSON-LD -	Semantic data output	Schema.org-based, machine-readable
Regex (re) -	String parsing	Extracts models, RAM, dimensions, etc.

4. How it works
- Launch Selenium with headless Chrome.

- Navigate to category pages (Laptops, TVs, Phones).

- Trigger lazy-loading via scrolling.

- Extract product info (name + price) with BeautifulSoup.

- Paginate until max pages reached.

- Save raw data into data/*.csv.

- Phase 2 – Data Transformation

- Read CSVs with Pandas.

- Clean & parse names with Regex (RAM, storage, screen size, etc.).

- Normalize prices into floats.

- Build Schema.org JSON-LD object (Product + Offer).

- Add specs as additionalProperty for flexibility.

- Save structured data into reforged_data/*.jsonld.

5. Prerequisites:
- Python 3.8+
- Google Chrome installed

6. Usage
- Run Scrapers in python scrapers/
  - Outputs raw CSVs in data/
-  Run reforgers
  - Outputs JSON-LD files in reforged_data/

7. Example JSON-LD Output
{
  "@context": "https://schema.org",
  "@type": "Product",
  "@id": "anhoch-laptops-1",
  "category": "Laptops",
  "name": "Notebook Dell Latitude 5540 i5-1335U/16GB/512GB SSD/15.6\" FHD/FRP/BacklitKB/Ubu",
  "offers": {
    "@type": "Offer",
    "price": null,
    "priceCurrency": null,
    "availability": "https://schema.org/InStock"
  },
  "brand": {
    "@type": "Brand",
    "name": "Dell"
  },
  "model": "Latitude 5540",
  "additionalProperty": [
    { "@type": "PropertyValue", "name": "Processor", "value": "i5-1335U" },
    { "@type": "PropertyValue", "name": "RAM", "value": "16GB" },
    { "@type": "PropertyValue", "name": "Storage", "value": "512GB SSD" },
    { "@type": "PropertyValue", "name": "Screen Size", "value": "15.6\"" }
  ],
  "description": "Dell Latitude 5540 with i5-1335U processor."
}

8. Why This Architecture?

Scrapers = volatile → only updated if site layout changes.

Reforgers = stable → maintain semantic modeling regardless of site UI.

Schema.org JSON-LD → machine-readable, reusable, SEO-friendly data.

This design makes the system modular, robust, and future-proof for new sources or categories.

9. Schema.org validator
Here is an example of the schema.org validator that validates the data whether or not consumable by search engines and knowledge graph systems
<img width="1919" height="904" alt="jsonldToReforgedData" src="https://github.com/user-attachments/assets/a0c3a912-b6f8-4cff-93e0-5dfbe4f72ed2" />


