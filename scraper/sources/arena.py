"""Coletor do Are.na (https://api.are.na) — API pública, sem anti-bot.

Diferente de Dribbble/Behance/Land-book (que bloqueiam scraping), o Are.na
é nativamente um acervo de referências visuais e expõe uma API REST pública.
Busca blocos por palavras-chave de design e mapeia para RawItem.
"""
from __future__ import annotations

import os
import time

import httpx

from .base import BROWSER_UA, RawItem, dedup_by_url

SEARCH_URL = "https://api.are.na/v2/search/blocks"
QUERIES = ["web design", "app ui", "landing page", "dashboard", "mobile ui"]
PER_QUERY = 24


def _image_url(block: dict) -> str:
    """Extrai a maior URL de imagem disponível de um bloco do Are.na."""
    image = block.get("image") or {}
    for key in ("large", "display", "original", "thumb"):
        url = (image.get(key) or {}).get("url")
        if url:
            return url
    return ""


def parse_blocks(blocks: list[dict], query: str = "") -> list[RawItem]:
    """Converte blocos do Are.na (classe Image/Link com imagem) em RawItem."""
    items: list[RawItem] = []
    for block in blocks:
        if block.get("class") not in ("Image", "Link"):
            continue
        image_url = _image_url(block)
        if not image_url:
            continue
        source = block.get("source") or {}
        provider = source.get("provider") or {}
        user = block.get("user") or {}
        block_id = block.get("id")
        url = source.get("url") or (f"https://www.are.na/block/{block_id}" if block_id else "")
        if not url:
            continue
        title = (
            block.get("title")
            or block.get("generated_title")
            or source.get("title")
            or "Are.na block"
        ).strip()
        author = (user.get("username") or provider.get("name") or "").strip()
        tags = [t for t in (query, "arena") if t]
        items.append(
            RawItem(title=title, url=url, source="arena", author=author, image_url=image_url, tags=tags)
        )
    return items


def fetch() -> list[RawItem]:
    items: list[RawItem] = []
    headers = {"User-Agent": BROWSER_UA, "Accept": "application/json"}
    # Token opcional: o Are.na serve conteúdo público sem auth, mas se um dia
    # exigir, basta definir o secret ARENA_TOKEN no repositório.
    token = os.environ.get("ARENA_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with httpx.Client(headers=headers, follow_redirects=True, timeout=30) as client:
        for query in QUERIES:
            try:
                resp = client.get(SEARCH_URL, params={"q": query, "per": PER_QUERY})
            except Exception as exc:
                print(f"  arena: erro em '{query}': {exc}")
                continue
            blocks = []
            if resp.status_code == 200:
                blocks = (resp.json() or {}).get("blocks", [])
            found = parse_blocks(blocks, query)
            print(f"  arena: '{query}' -> HTTP {resp.status_code}, "
                  f"{len(blocks)} blocos, {len(found)} com imagem")
            items.extend(found)
            time.sleep(1)  # educação com a API
    return dedup_by_url(items)
