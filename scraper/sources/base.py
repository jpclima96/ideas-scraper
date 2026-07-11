"""Contrato comum dos coletores: cada fonte expõe fetch() -> list[RawItem]."""
from __future__ import annotations

from dataclasses import dataclass, field

USER_AGENT = (
    "ideas-scraper/0.1 (coletor pessoal de referências de design; "
    "+https://github.com/jpclima96/ideas-scraper)"
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
