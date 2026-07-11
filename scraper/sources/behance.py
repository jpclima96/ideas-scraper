"""Coletor do Behance via Playwright (a API oficial foi descontinuada pela Adobe).

Fonte frágil por natureza (anti-bot, HTML dinâmico): qualquer erro aqui é
tolerado pelo orquestrador e as demais fontes seguem normalmente.
"""
from __future__ import annotations

from urllib.parse import quote

from .base import BROWSER_UA, RawItem, dedup_by_url

SEARCHES = ["web design", "mobile app ui"]
MAX_PER_SEARCH = 30


def _best_image(img) -> str:
    """Extrai a maior URL de imagem de um <img>, cobrindo lazy-load (srcset/data-src)."""
    if img is None:
        return ""
    srcset = img.get_attribute("srcset") or ""
    if srcset:
        # "url1 320w, url2 640w" -> pega a última (maior)
        last = srcset.split(",")[-1].strip().split(" ")[0]
        if last.startswith("http"):
            return last
    for attr in ("src", "data-src", "data-srcset"):
        val = (img.get_attribute(attr) or "").split(" ")[0]
        if val.startswith("http"):
            return val
    return ""


def fetch() -> list[RawItem]:
    from playwright.sync_api import sync_playwright  # import tardio: só quem roda precisa

    items: list[RawItem] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=BROWSER_UA)
        for query in SEARCHES:
            page.goto(
                f"https://www.behance.net/search/projects?search={quote(query)}",
                timeout=60_000,
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(4_000)
            # Rola a página para disparar o carregamento lazy das imagens.
            for _ in range(4):
                page.mouse.wheel(0, 4_000)
                page.wait_for_timeout(1_500)

            count = 0
            for card in page.query_selector_all("a[href*='/gallery/']"):
                href = card.get_attribute("href") or ""
                if "/gallery/" not in href:
                    continue
                url = href if href.startswith("http") else f"https://www.behance.net{href}"
                img = card.query_selector("img")
                image_url = _best_image(img)
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
        browser.close()

    unique = dedup_by_url(items)
    with_img = sum(1 for it in unique if it.image_url)
    sample = next((it.image_url for it in unique if it.image_url), "")
    print(f"  behance: {len(unique)} itens, {with_img} com imagem; ex: {sample[:90]}")
    return unique
