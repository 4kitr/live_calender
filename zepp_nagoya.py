import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://www.zepp.co.jp/hall/nagoya/schedule/"

headers = {
    "User-Agent": "LiveCalendar/1.0"
}

response = requests.get(URL, headers=headers, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

links = soup.select('a[href*="/schedule/single/"]')

print(f"公演詳細リンク数: {len(links)}")

for link in links:
    detail_url = urljoin(URL, link["href"])
    print("\n--------------------")
    print("詳細URL:", detail_url)

    parent = link

    for level in range(1, 7):
        parent = parent.parent

        if parent is None:
            break

        text = " ".join(parent.stripped_strings)
        print(f"親要素{level}:", text[:500])

        if re.search(r"\d{4}\s+\d{1,2}\.\d{1,2}", text):
            break