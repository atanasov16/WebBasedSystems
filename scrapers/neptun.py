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


def scrape_neptun_products(category_url, category_name, max_pages=15):
    driver = setup_driver()
    all_products = []
    page = 1

    while page <= max_pages:
        url = f"{category_url}?page={page}"
        print(f"Scraping {url}")

        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.white-box"))
            )

            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2)")
            time.sleep(random.uniform(1, 2))

            soup = BeautifulSoup(driver.page_source, "lxml")
            products = soup.select("div.white-box")

            if not products:
                print(f"No products found on page {page}")
                break

            for product in products:
                try:
                    # Extract product name
                    name_elem = product.select_one("h2.product-list-item__content--title")
                    name = name_elem.get_text(strip=True) if name_elem else "N/A"

                    # Extract discounted price (HaPPy цена)
                    price_elem = product.select_one(
                        "div.product-price__amount span.product-price__amount--value.ng-binding")
                    price = price_elem.get_text(strip=True) + " ден." if price_elem else "N/A"

                    all_products.append({
                        "name": name,
                        "price": price
                    })

                except Exception as e:
                    print(f"Error processing product: {e}")
                    continue

            page += 1
            time.sleep(random.uniform(2, 4))  # Random delay between pages

        except Exception as e:
            print(f"Error loading page {page}: {str(e)}")
            break

    driver.quit()

    os.makedirs("../data", exist_ok=True)
    filename = f"../data/neptun_{category_name.lower().replace(' ', '_')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "price"])
        writer.writeheader()
        writer.writerows(all_products)

    print(f"Scraped {len(all_products)} {category_name} products. Saved to {filename}")
    return all_products


def scrape_tvs():
    url = "https://www.neptun.mk/televizori.nspx"
    return scrape_neptun_products(url, "TVs", max_pages=13)


def scrape_phones():
    url = "https://www.neptun.mk/mobilni_telefoni.nspx"
    return scrape_neptun_products(url, "Phones", max_pages=11)


def scrape_laptops():
    url = "https://www.neptun.mk/prenosni_kompjuteri.nspx"
    return scrape_neptun_products(url, "Laptops", max_pages=7)


if __name__ == "__main__":
    print("Starting Neptun.mk scraping...")

    print("\nScraping TVs...")
    tvs = scrape_tvs()

    print("\nScraping Phones...")
    phones = scrape_phones()

    print("\nScraping Laptops...")
    laptops = scrape_laptops()

    print("\nScraping completed!")
    print(f"Total TVs scraped: {len(tvs)}")
    print(f"Total Phones scraped: {len(phones)}")
    print(f"Total Laptops scraped: {len(laptops)}")