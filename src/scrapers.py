# src/scrapers.py
import requests
from bs4 import BeautifulSoup

from typing import Optional

HEADERS = {'User-Agent': 'TruthLensBot/1.0 (+https://example.com)'}

def scrape_url(url: str) -> str:
    
    # fallback to requests + BeautifulSoup
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        # remove scripts/styles
        for tag in soup(['script','style','noscript','header','footer','iframe','aside','nav']):
            tag.decompose()
        # prefer <article>
        article_tag = soup.find('article')
        if article_tag:
            text = article_tag.get_text(separator=' ')
        else:
            paragraphs = soup.find_all('p')
            text = " ".join(p.get_text(separator=' ') for p in paragraphs)
        title = soup.title.string if soup.title else ''
        content = (title + ". " + text).strip()
        return content
    except Exception:
        return ""
