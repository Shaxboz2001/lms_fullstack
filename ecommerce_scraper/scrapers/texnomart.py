from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time


def scrape_texnomart():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # fon rejimida (agar ko‘rmoqchi bo‘lsang, bu qatorni komment qil)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # ✅ ChromeDriver avtomatik yuklash
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    url = "https://texnomart.uz/ru/katalog/telefony-i-gadzhety/smartfony"
    driver.get(url)
    time.sleep(3)  # sahifa yuklanishi uchun kutish

    products = []

    while True:
        time.sleep(2)

        items = driver.find_elements(By.CSS_SELECTOR, "div.product-item")
        for item in items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "span.product-name").text.strip()
            except:
                name = None
            try:
                price = item.find_element(By.CSS_SELECTOR, "span.price").text.strip()
            except:
                price = None
            try:
                link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
            except:
                link = None

            products.append({
                "market": "Texnomart",
                "name": name,
                "price": price,
                "link": link
            })

        # Keyingi sahifa bor-yo‘qligini tekshiramiz
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "a[rel='next']")
            if "disabled" in next_btn.get_attribute("class"):
                break
            else:
                next_btn.click()
                time.sleep(3)
        except:
            break

    driver.quit()
    return products


if __name__ == "__main__":
    data = scrape_texnomart()
    print(f"✅ Texnomart: {len(data)} ta mahsulot topildi")
    for d in data[:5]:  # faqat dastlabki 5 ta mahsulotni chiqaramiz
        print(d)
