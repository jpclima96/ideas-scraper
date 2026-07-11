from scraper.sources.arena import parse_blocks

# Amostra representativa da resposta de /v2/search/blocks do Are.na.
SAMPLE = [
    {
        "id": 111,
        "class": "Image",
        "title": "Fintech Dashboard",
        "image": {
            "thumb": {"url": "https://arena.img/thumb.jpg"},
            "large": {"url": "https://arena.img/large.jpg"},
        },
        "source": {"url": "https://example.com/fintech", "title": "Fintech"},
        "user": {"username": "designer1"},
    },
    {
        "id": 222,
        "class": "Link",
        "title": "Landing Page",
        "image": {"display": {"url": "https://arena.img/display.png"}},
        "source": {"url": "", "provider": {"name": "Acme"}},
        "user": {},
    },
    # Texto: deve ser ignorado (sem imagem, classe Text)
    {"id": 333, "class": "Text", "content": "só texto"},
    # Imagem sem URL utilizável: ignorado
    {"id": 444, "class": "Image", "image": {"thumb": {"url": None}}},
]


def test_parse_blocks_extracts_image_blocks():
    items = parse_blocks(SAMPLE, query="web design")
    assert len(items) == 2

    first = items[0]
    assert first.title == "Fintech Dashboard"
    assert first.source == "arena"
    assert first.url == "https://example.com/fintech"
    assert first.image_url == "https://arena.img/large.jpg"  # prefere 'large'
    assert first.author == "designer1"
    assert "web design" in first.tags


def test_parse_blocks_fallbacks():
    items = parse_blocks(SAMPLE)
    link = items[1]
    # sem source.url -> cai para a URL do bloco no Are.na
    assert link.url == "https://www.are.na/block/222"
    assert link.image_url == "https://arena.img/display.png"
    assert link.author == "Acme"  # username vazio -> provider.name


def test_parse_blocks_skips_non_image():
    assert parse_blocks([{"id": 1, "class": "Text"}]) == []
