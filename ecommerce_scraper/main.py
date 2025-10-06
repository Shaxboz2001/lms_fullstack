from scrapers.texnomart import scrape_texnomart
from scrapers.mediapark import scrape_mediapark
from scrapers.olx import scrape_olx
from scrapers.uzum import scrape_uzum
from scrapers.yandex import scrape_yandex
from db import close_db

if __name__ == "__main__":
    scrape_texnomart()
    scrape_mediapark()
    scrape_olx()
    scrape_uzum()
    scrape_yandex()

    close_db()
