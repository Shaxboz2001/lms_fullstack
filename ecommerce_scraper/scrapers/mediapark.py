import requests
from bs4 import BeautifulSoup
from utils import clean_price
from db import insert_product

def scrape_mediapark():
    url = "https://mediapark.uz/catalog/telefony"  # Telefonlar bo‘limi
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    for item in soup.select(".product-card"):
        try:
            name = item.select_one(".product-title").get_text(strip=True)
            price = clean_price(item.select_one(".price").get_text(strip=True))

            product = {
                "product_name": name,
                "brand": name.split()[0],
                "category": "Smartphone",
                "price": price,
                "market": "Mediapark"
            }
            insert_product(product)
        except Exception as e:
            print("❌ Error parsing Mediapark:", e)

    print("✅ Mediapark scraping tugadi")
