from playwright.sync_api import sync_playwright
from utils import clean_price
from db import insert_product

def scrape_yandex():
    url = "https://market.yandex.ru/catalog--smartfony/26893750"  # Smartfonlar bo‘limi

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        items = page.query_selector_all(".n-snippet-card2")  # class yangilanishi mumkin
        for item in items:
            try:
                name = item.query_selector(".n-snippet-card2__title").inner_text().strip()
                price = clean_price(item.query_selector(".price").inner_text().strip())

                product = {
                    "product_name": name,
                    "brand": name.split()[0],
                    "category": "Smartphone",
                    "price": price,
                    "market": "Yandex Market"
                }
                insert_product(product)
            except Exception as e:
                print("❌ Error parsing Yandex:", e)

        browser.close()

    print("✅ Yandex Market scraping tugadi")
