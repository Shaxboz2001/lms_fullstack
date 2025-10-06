import requests
from bs4 import BeautifulSoup
import psycopg2


def scrape_olx_jobs():
    url = "https://www.olx.uz/uz/rabota/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    jobs = []
    for ad in soup.select('.css-19ucd76'):
        title = ad.select_one('.css-1bbgabe').text if ad.select_one('.css-1bbgabe') else ''
        location = ad.select_one('.css-1a4brun').text if ad.select_one('.css-1a4brun') else ''
        link = 'https://www.olx.uz' + ad.get('href')
        jobs.append((title, location, link))

    return jobs
    