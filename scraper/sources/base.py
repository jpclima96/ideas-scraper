"""Contrato comum dos coletores: cada fonte expõe fetch() -> list[RawItem]."""
from __future__ import annotations

from dataclasses import dataclass, field

# Mantido em ASCII: httpx recusa cabeçalhos com caracteres não-ASCII
# (um acento aqui quebrava o Land-book e o download de todas as thumbs).
USER_AGENT = (
    "ideas-scraper/0.1 (personal design reference collector; "
    "+https://github.com/jpclima96/ideas-scraper)"
)

# Vários sites (Land-book, CDNs de imagem) respondem 403 a User-Agents que
# não sejam de navegador. Usamos este UA realista para as requisições HTTP.
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class RawItem:
    title: str
    url: str
    source: str
    author: str = ""
    image_url: str = ""
    tags: list[str] = field(default_factory=list)


def dedup_by_url(items: list[RawItem]) -> list[RawItem]:
    seen: set[str] = set()
    unique = []
    for item in items:
        if item.url in seen:
            continue
        seen.add(item.url)
        unique.append(item)
    return unique
