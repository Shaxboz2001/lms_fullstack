import requests
from bs4 import BeautifulSoup
from utils import clean_price
from db import insert_product

def scrape_olx():
    url = "https://www.olx.uz/elektronika/telefonlar/"  # Telefonlar bo‘limi
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")

    for item in soup.select(".css-1sw7q4x"):  # OLX item class
        try:
            name = item.select_one("h6").get_text(strip=True)
            price = clean_price(item.select_one(".price").get_text(strip=True))

            product = {
                "product_name": name,
                "brand": name.split()[0],
                "category": "Smartphone",
                "price": price,
                "market": "OLX"
            }
            insert_product(product)
        except Exception as e:
            print("❌ Error parsing OLX:", e)

    print("✅ OLX scraping tugadi")
