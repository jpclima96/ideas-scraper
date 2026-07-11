"""Coletor do Dribbble via feeds RSS públicos (a API v2 só expõe shots da própria conta)."""
from __future__ import annotations

import time

import feedparser
import httpx
from bs4 import BeautifulSoup

from .base import BROWSER_UA, RawItem, dedup_by_url

FEEDS = [
    "https://dribbble.com/shots/popular.rss",
    "https://dribbble.com/shots/recent.rss",
    "https://dribbble.com/tags/web-design.rss",
    "https://dribbble.com/tags/mobile-app.rss",
    "https://dribbble.com/tags/landing-page.rss",
    "https://dribbble.com/tags/dashboard.rss",
]


def parse_feed(parsed: feedparser.FeedParserDict) -> list[RawItem]:
    items = []
    for entry in parsed.get("entries", []):
        url = entry.get("link", "")
        title = (entry.get("title") or "").strip()
        if not url or not title:
            continue
        summary = entry.get("summary", "") or entry.get("description", "")
        image_url = ""
        if summary:
            img = BeautifulSoup(summary, "html.parser").find("img")
            if img:
                image_url = img.get("src", "")
        tags = [t.get("term", "") for t in entry.get("tags", []) if t.get("term")]
        items.append(
            RawItem(
                title=title,
                url=url,
                source="dribbble",
                author=(entry.get("author") or "").strip(),
                image_url=image_url,
                tags=tags,
            )
        )
    return items


def fetch() -> list[RawItem]:
    items: list[RawItem] = []
    headers = {
        "User-Agent": BROWSER_UA,
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
    }
    with httpx.Client(headers=headers, follow_redirects=True, timeout=30) as client:
        for feed_url in FEEDS:
            try:
                resp = client.get(feed_url)
            except Exception as exc:
                print(f"  dribbble: erro em {feed_url}: {exc}")
                continue
            parsed = feedparser.parse(resp.content)
            found = parse_feed(parsed)
            print(f"  dribbble: {feed_url} -> HTTP {resp.status_code}, "
                  f"{len(resp.content)} bytes, {len(found)} itens")
            items.extend(found)
            time.sleep(2)  # educação com o servidor
    return dedup_by_url(items)
