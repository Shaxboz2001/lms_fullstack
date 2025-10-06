from playwright.sync_api import sync_playwright
from utils import clean_price
from db import insert_product

def scrape_uzum():
    url = "https://uzum.uz/uz/category/smartfony-12345"  # Telefon kategoriyasi

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        items = page.query_selector_all(".product-card")
        for item in items:
            try:
                name = item.query_selector(".product-title").inner_text().strip()
                price = clean_price(item.query_selector(".price").inner_text().strip())

                product = {
                    "product_name": name,
                    "brand": name.split()[0],
                    "category": "Smartphone",
                    "price": price,
                    "market": "Uzum Market"
                }
                insert_product(product)
            except Exception as e:
                print("❌ Error parsing Uzum:", e)

        browser.close()

    print("✅ Uzum Market scraping tugadi")
