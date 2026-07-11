from scraper.main import merge_new
from scraper.models import Reference, load_references, make_id, save_references
from scraper.sources.base import RawItem


def _raw(url: str, title: str = "Cool Shot") -> RawItem:
    return RawItem(title=title, url=url, source="dribbble", image_url="", tags=["web"])


def test_merge_skips_duplicate_urls_in_batch():
    pairs = merge_new([], [_raw("https://x.com/a"), _raw("https://x.com/a"), _raw("https://x.com/b")])
    assert len(pairs) == 2


def test_merge_skips_already_known():
    url = "https://dribbble.com/shots/123"
    existing = Reference(
        id=make_id(url), title="t", author="a", url=url, source="dribbble", collected_at="2026-01-01"
    )
    pairs = merge_new([existing], [_raw(url)])
    assert pairs == []


def test_save_load_roundtrip_keeps_items_unique(tmp_path):
    path = tmp_path / "references.json"
    pairs = merge_new([], [_raw("https://x.com/a")], today="2026-07-11")
    save_references([ref for ref, _ in pairs], path)

    loaded = load_references(path)
    assert len(loaded) == 1
    assert loaded[0].url == "https://x.com/a"

    # segunda rodada com o mesmo item não adiciona nada
    assert merge_new(loaded, [_raw("https://x.com/a")]) == []
