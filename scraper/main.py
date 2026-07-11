"""Orquestrador: coleta de todas as fontes, deduplica, gera thumbs e salva o JSON."""
from __future__ import annotations

import datetime
import traceback

from . import thumbs
from .categorize import categorize
from .models import Reference, load_references, make_id, save_references
from .sources import ACTIVE_SOURCES
from .sources.base import RawItem


def merge_new(
    existing: list[Reference], raw_items: list[RawItem], today: str | None = None
) -> list[tuple[Reference, str]]:
    """Converte itens crus ainda não presentes no acervo. Retorna pares (ref, image_url)."""
    today = today or datetime.date.today().isoformat()
    known = {r.id for r in existing}
    added: list[tuple[Reference, str]] = []
    for item in raw_items:
        ref_id = make_id(item.url)
        if ref_id in known:
            continue
        known.add(ref_id)
        platform, type_, styles = categorize(item.title, item.tags)
        ref = Reference(
            id=ref_id,
            title=item.title,
            author=item.author,
            url=item.url,
            source=item.source,
            platform=platform,
            type=type_,
            styles=styles,
            tags=item.tags,
            collected_at=today,
        )
        added.append((ref, item.image_url))
    return added


def run() -> None:
    refs = load_references()
    print(f"Acervo atual: {len(refs)} referências")

    new_refs: list[Reference] = []
    for name, fetch in ACTIVE_SOURCES.items():
        print(f"\n== {name} ==")
        try:
            raw = fetch()
        except Exception:
            print(f"{name}: FALHOU — seguindo com as demais fontes")
            traceback.print_exc()
            continue
        pairs = merge_new(refs + new_refs, raw)
        print(f"{name}: {len(raw)} coletados, {len(pairs)} novos")
        for ref, image_url in pairs:
            ref.thumb = thumbs.save_thumb(ref.id, image_url)
            new_refs.append(ref)

    if new_refs:
        save_references(refs + new_refs)
    print(f"\nTotal de novos itens: {len(new_refs)} (acervo: {len(refs) + len(new_refs)})")


if __name__ == "__main__":
    run()
