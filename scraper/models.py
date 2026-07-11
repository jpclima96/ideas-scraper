"""Modelo de dados e persistência do acervo em data/references.json."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REFERENCES_PATH = DATA_DIR / "references.json"
THUMBS_DIR = DATA_DIR / "thumbs"


def make_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


@dataclass
class Reference:
    id: str
    title: str
    author: str
    url: str
    source: str
    thumb: str = ""
    platform: str = "unknown"
    type: str = "other"
    styles: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    collected_at: str = ""


def load_references(path: Path = REFERENCES_PATH) -> list[Reference]:
    if not path.exists():
        return []
    return [Reference(**item) for item in json.loads(path.read_text(encoding="utf-8"))]


def save_references(refs: list[Reference], path: Path = REFERENCES_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(refs, key=lambda r: (r.collected_at, r.id), reverse=True)
    payload = json.dumps([asdict(r) for r in ordered], ensure_ascii=False, indent=1)
    path.write_text(payload + "\n", encoding="utf-8")
