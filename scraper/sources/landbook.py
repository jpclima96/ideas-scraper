"""Coletor do Land-book (galeria de landing pages) via HTML estático."""
from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from .base import BROWSER_UA, RawItem, dedup_by_url

URL = "https://land-book.com/"


def parse_html(html: str) -> list[RawItem]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for anchor in soup.select("a[href*='/websites/']"):
        img = anchor.find("img")
        if not img:
            continue
        href = anchor.get("href", "")
        url = href if href.startswith("http") else f"https://land-book.com{href}"
        title = (img.get("alt") or anchor.get_text(strip=True) or url).strip()
        image_url = img.get("src") or img.get("data-src") or ""
        if image_url.startswith("/"):
            image_url = f"https://land-book.com{image_url}"
        items.append(
            RawItem(title=title, url=url, source="landbook", image_url=image_url, tags=["web", "website"])
        )
    return dedup_by_url(items)


def fetch() -> list[RawItem]:
    resp = httpx.get(
        URL,
        headers={"User-Agent": BROWSER_UA, "Accept-Language": "en-US,en;q=0.9"},
        follow_redirects=True,
        timeout=30,
    )
    print(f"  landbook: HTTP {resp.status_code}, {len(resp.text)} bytes")
    resp.raise_for_status()
    items = parse_html(resp.text)
    print(f"  landbook: {len(items)} itens após parse (seletor a[href*='/websites/'])")
    return items
