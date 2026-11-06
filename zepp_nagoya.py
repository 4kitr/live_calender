import json
import re
import requests
from datetime import date
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

URL = "https://www.zepp.co.jp/hall/nagoya/schedule/"
HEADERS = {"User-Agent": "LiveCalendar/1.0"}

response = requests.get(URL, headers=HEADERS, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")
links = soup.select('a[href*="/schedule/single/"]')

events = []
seen = set()

date_pattern = re.compile(
    r"(20\d{2})\s+(\d{1,2})\.(\d{1,2})\s+"
    r"(MON|TUE|WED|THU|FRI|SAT|SUN)",
    re.I
)

for link in links:
    node = link
    text = ""

    # 公演情報を含む親要素を探す
    for _ in range(7):
        if node is None:
            break

        candidate = " ".join(node.stripped_strings)

        if date_pattern.search(candidate):
            text = candidate
            break

        node = node.parent

    match = date_pattern.search(text)
    if not match:
        continue

    year, month, day = map(int, match.groups()[:3])
    event_date = date(year, month, day)

    if event_date < date.today():
        continue

    rest = text[match.end():]

    # 開場・開演時間
    open_match = re.search(r"\[OPEN\]\s*(\d{1,2}:\d{2})", rest)
    start_match = re.search(r"\[START\]\s*(\d{1,2}:\d{2})", rest)

    # 出演者・公演名（暫定）
    artist = re.split(
        r"\[OPEN\]|\[START\]|\[PRICE\]|\[お問合せ\]",
        rest
    )[0].strip()

    artist = re.sub(r"^TODAY\s*", "", artist)

    if not artist:
        continue

    event = {
        "date": event_date.isoformat(),
        "artist": artist,
        "venue": "Zepp Nagoya",
        "area": "愛知",
        "genre": "その他",
        "open": open_match.group(1) if open_match else "",
        "start": start_match.group(1) if start_match else "",
        "url": urljoin(URL, link.get("href", "")),
        "source": "Zepp Nagoya公式"
    }

    key = (event["date"], event["artist"])

    if key not in seen:
        seen.add(key)
        events.append(event)

if not events:
    raise RuntimeError("公演情報を取得できませんでした。既存データは変更していません。")

# 既存のイベント情報を残して追加
path = Path("events.json")

if path.exists():
    existing = json.loads(path.read_text(encoding="utf-8"))
else:
    existing = []

if not isinstance(existing, list):
    raise ValueError("events.jsonの形式が正しくありません")

merged = existing + events

final = []
keys = set()

for event in merged:
    key = (
        event["date"],
        event["venue"].lower(),
        event["artist"].lower()
    )

    if key not in keys:
        keys.add(key)
        final.append(event)

path.write_text(
    json.dumps(final, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"取得件数: {len(events)}")
print(f"保存後の総件数: {len(final)}")
