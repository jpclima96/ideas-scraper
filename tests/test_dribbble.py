from pathlib import Path

import feedparser

from scraper.sources.dribbble import parse_feed

FIXTURE = Path(__file__).parent / "fixtures" / "dribbble.rss"


def test_parse_feed_extracts_items():
    items = parse_feed(feedparser.parse(FIXTURE.read_text()))
    assert len(items) == 3

    first = items[0]
    assert first.title == "Fintech Dashboard Dark Mode"
    assert first.url == "https://dribbble.com/shots/11111-fintech-dashboard"
    assert first.author == "Jane Designer"
    assert first.image_url == "https://cdn.dribbble.com/userupload/11111/file/original.png"
    assert set(first.tags) == {"dashboard", "dark"}


def test_parse_feed_tolerates_missing_image():
    items = parse_feed(feedparser.parse(FIXTURE.read_text()))
    assert items[2].image_url == ""
