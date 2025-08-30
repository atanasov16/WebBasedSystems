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

CHROMEDRIVER_PATH = r"C:\Users\dakag\Downloads\chromedriver-win64\chromedriver.exe"


def scrape_setec_products(category_url, category_name, max_pages=20):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })

    all_products = []
    page = 1

    while page <= max_pages:
        url = f"{category_url}?page={page}"
        print(f"Scraping {url}")

        try:
            driver.get(url)

            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.relative.bg-white.p-4"))
            )

            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2)")
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, "lxml")
            products = soup.select("div.relative.bg-white.p-4")

            if not products:
                if page == 1:
                    print("No products found on first page - check URL or if blocked")
                break

            for p in products:
                name = p.select_one("h3").get_text(strip=True) if p.select_one("h3") else ""
                price = p.select_one("span.text-xl").get_text(strip=True) if p.select_one("span.text-xl") else ""
                all_products.append({"name": name, "price": price})

            page += 1
            time.sleep(2)

        except Exception as e:
            print(f"Error on page {page}: {str(e)}")
            break

    driver.quit()

    os.makedirs("../data", exist_ok=True)
    filename = f"../data/setec_{category_name.lower().replace(' ', '_')}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "price"])
        writer.writeheader()
        writer.writerows(all_products)

    print(f"Scraped {len(all_products)} {category_name} products. Saved to {filename}")
    return all_products


def scrape_oled_tvs():
    url = "https://setec.mk/category/oled-30334"
    return scrape_setec_products(url, "OLED_TVs", max_pages=5)


def scrape_laptops():
    url = "https://setec.mk/category/prenosni-20komp-d1-98uteri-3"
    return scrape_setec_products(url, "Laptops", max_pages=20)


def scrape_smartphones():
    url = "https://setec.mk/category/mobilni-20telefoni-67"
    return scrape_setec_products(url, "Smartphones", max_pages=20)


if __name__ == "__main__":
    print("Starting Setec.mk scraping...")

    print("\nScraping OLED TVs...")
    oled_tvs = scrape_oled_tvs()

    print("\nScraping Laptops...")
    laptops = scrape_laptops()

    print("\nScraping Smartphones...")
    smartphones = scrape_smartphones()

    print("\nScraping completed!")
    print(f"Total OLED TVs scraped: {len(oled_tvs)}")
    print(f"Total Laptops scraped: {len(laptops)}")
    print(f"Total Smartphones scraped: {len(smartphones)}")