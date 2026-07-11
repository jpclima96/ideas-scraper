"""Coletor do Behance via Playwright (a API oficial foi descontinuada pela Adobe).

Fonte frágil por natureza (anti-bot, HTML dinâmico): qualquer erro aqui é
tolerado pelo orquestrador e as demais fontes seguem normalmente.
"""
from __future__ import annotations

from urllib.parse import quote

from .base import USER_AGENT, RawItem, dedup_by_url

SEARCHES = ["web design", "mobile app ui"]
MAX_PER_SEARCH = 30


def fetch() -> list[RawItem]:
    from playwright.sync_api import sync_playwright  # import tardio: só quem roda precisa

    items: list[RawItem] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=USER_AGENT)
        for query in SEARCHES:
            page.goto(
                f"https://www.behance.net/search/projects?search={quote(query)}",
                timeout=60_000,
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(5_000)  # ritmo lento de propósito
            count = 0
            for card in page.query_selector_all("a[href*='/gallery/']"):
                href = card.get_attribute("href") or ""
                if "/gallery/" not in href:
                    continue
                url = href if href.startswith("http") else f"https://www.behance.net{href}"
                img = card.query_selector("img")
                image_url = (img.get_attribute("src") if img else "") or ""
                title = (
                    (img.get_attribute("alt") if img else "")
                    or card.get_attribute("aria-label")
                    or card.inner_text().split("\n")[0]
                    or url
                ).strip()
                if not title:
                    continue
                items.append(
                    RawItem(title=title, url=url, source="behance", image_url=image_url, tags=[query])
                )
                count += 1
                if count >= MAX_PER_SEARCH:
                    break
            page.wait_for_timeout(4_000)
        browser.close()
    return dedup_by_url(items)
