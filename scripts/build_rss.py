import re
import os
import html
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.utils import format_datetime

INPUT = "feeds.txt"
OUTDIR = "output"

UA = "rss-builder-bot/1.0"

def parse_input():
    groups = {}
    current = None
    with open(INPUT, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                current = line[1:-1]
                groups[current] = []
            else:
                groups[current].append(line)
    return groups

def fetch(url):
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return r.text

def extract(html_text, url):
    soup = BeautifulSoup(html_text, "html.parser")

    title = soup.title.string.strip() if soup.title else url

    # try og image
    og = soup.find("meta", property="og:image")
    thumb = og["content"] if og else None

    if not thumb:
        img = soup.find("img")
        if img and img.get("src"):
            thumb = img["src"]

    # date
    pub = datetime.utcnow()

    return title, thumb, pub

def build_feed(name, urls):
    items = []

    for url in urls:
        try:
            html_text = fetch(url)
            title, thumb, pub = extract(html_text, url)

            media = ""
            if thumb:
                media = f'<media:content url="{html.escape(thumb)}" medium="image" />'

            item = f"""
            <item>
              <title>{html.escape(title)}</title>
              <link>{url}</link>
              <guid>{url}</guid>
              <pubDate>{format_datetime(pub)}</pubDate>
              {media}
            </item>
            """
            items.append(item)
        except Exception as e:
            print("ERR", url, e)

    rss = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
 xmlns:media="http://search.yahoo.com/mrss/">
<channel>
<title>{html.escape(name)}</title>
<link>https://example.com/</link>
<description>Generated feed</description>
{''.join(items)}
</channel>
</rss>
"""

    os.makedirs(OUTDIR, exist_ok=True)
    with open(f"{OUTDIR}/{name}.xml", "w", encoding="utf-8") as f:
        f.write(rss)

def main():
    groups = parse_input()
    for name, urls in groups.items():
        build_feed(name, urls)

if __name__ == "__main__":
    main()
