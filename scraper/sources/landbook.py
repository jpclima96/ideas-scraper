"""Coletor do Land-book (galeria de landing pages) via HTML estático."""
from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from .base import USER_AGENT, RawItem, dedup_by_url

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
    resp = httpx.get(URL, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=30)
    resp.raise_for_status()
    return parse_html(resp.text)
