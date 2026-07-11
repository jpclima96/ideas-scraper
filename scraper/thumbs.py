"""Download e geração de thumbnails webp (guardamos só a thumb + link, nunca a arte original)."""
from __future__ import annotations

import io

import httpx
from PIL import Image

from .models import THUMBS_DIR
from .sources.base import USER_AGENT

THUMB_WIDTH = 400


def save_thumb(ref_id: str, image_url: str, client: httpx.Client | None = None) -> str:
    """Baixa image_url e salva data/thumbs/<id>.webp. Retorna o caminho relativo ou "" se falhar."""
    if not image_url:
        return ""
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    dest = THUMBS_DIR / f"{ref_id}.webp"
    rel = f"thumbs/{ref_id}.webp"
    if dest.exists():
        return rel
    own_client = client is None
    client = client or httpx.Client(
        headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=30
    )
    try:
        resp = client.get(image_url)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        if img.width > THUMB_WIDTH:
            img = img.resize((THUMB_WIDTH, round(img.height * THUMB_WIDTH / img.width)))
        img.save(dest, "WEBP", quality=80)
        return rel
    except Exception as exc:  # thumb é opcional: item continua válido sem imagem
        print(f"  ! thumb falhou ({image_url}): {exc}")
        return ""
    finally:
        if own_client:
            client.close()
