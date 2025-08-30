from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv
import os
import random

# Path to your ChromeDriver
CHROMEDRIVER_PATH = r"C:\Users\dakag\Downloads\chromedriver-win64\chromedriver.exe"


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def scrape_anhoch_products(category_url, category_name, max_pages=1):
    driver = setup_driver()
    all_products = []
    page = 1

    while page <= max_pages:
        url = f"{category_url}&page={page}"
        print(f"Scraping {url}")

        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-card"))
            )

            # Scroll to trigger lazy loading
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 500)")
                time.sleep(random.uniform(0.5, 1.5))

            soup = BeautifulSoup(driver.page_source, "lxml")
            products = soup.select("div.product-card")

            if not products:
                print(f"No products found on page {page}")
                break

            for product in products:
                try:
                    name_elem = product.select_one("a.product-name h6")
                    name = name_elem.get_text(strip=True) if name_elem else "N/A"

                    price_elem = product.select_one("div.product-price")
                    price = price_elem.get_text(strip=True) if price_elem else "N/A"

                    all_products.append({
                        "name": name,
                        "price": price
                    })

                except Exception as e:
                    print(f"Error processing product: {e}")
                    continue

            page += 1
            time.sleep(random.uniform(2, 4))

        except Exception as e:
            print(f"Error loading page {page}: {str(e)}")
            break

    driver.quit()

    os.makedirs("../data", exist_ok=True)
    filename = f"../data/anhoch_{category_name.lower().replace(' ', '_')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "price"])
        writer.writeheader()
        writer.writerows(all_products)

    print(f"Scraped {len(all_products)} {category_name} products. Saved to {filename}")
    return all_products


def scrape_laptops():
    url = "https://www.anhoch.com/categories/site-laptopi/products?brand=&attribute=&toPrice=324980&inStockOnly=2&sort=latest&perPage=50"
    return scrape_anhoch_products(url, "Laptops", max_pages=6)


def scrape_tvs():
    url = "https://www.anhoch.com/categories/Televisions/products?brand=&attribute=&toPrice=324980&inStockOnly=2&sort=latest&perPage=50"
    return scrape_anhoch_products(url, "TVs", max_pages=4)


def scrape_phones():
    url = "https://www.anhoch.com/categories/mobilni-telefoni/products?brand=&attribute=&toPrice=324980&inStockOnly=2&sort=latest&perPage=50"
    return scrape_anhoch_products(url, "Phones", max_pages=6)


if __name__ == "__main__":
    print("Starting Anhoch.com scraping...")

    print("\nScraping Laptops...")
    laptops = scrape_laptops()

    print("\nScraping TVs...")
    tvs = scrape_tvs()

    print("\nScraping Phones...")
    phones = scrape_phones()

    print("\nScraping completed!")
    print(f"Total Laptops scraped: {len(laptops)}")
    print(f"Total TVs scraped: {len(tvs)}")
    print(f"Total Phones scraped: {len(phones)}")