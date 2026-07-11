from scraper.categorize import categorize


def test_dashboard_web():
    platform, type_, styles = categorize("Fintech Analytics Dashboard", ["dashboard", "dark"])
    assert platform == "web"
    assert type_ == "dashboard"
    assert "dark" in styles


def test_mobile_app():
    platform, type_, styles = categorize("Banking App iOS", ["mobile", "fintech"])
    assert platform == "mobile"
    assert type_ == "app"


def test_landing_page():
    platform, type_, _ = categorize("SaaS Landing Page Hero", ["web design"])
    assert platform == "web"
    assert type_ == "landing"


def test_word_boundary_no_false_positive():
    # "happy" não pode casar com a keyword "app"
    platform, type_, _ = categorize("Happy Halloween Illustration", [])
    assert platform == "unknown"
    assert type_ == "other"


def test_mobile_without_type_defaults_to_app():
    _, type_, _ = categorize("Smartwatch concept", [])
    assert type_ == "app"


def test_styles_multiple():
    _, _, styles = categorize("Minimal dark 3D website", [])
    assert {"minimal", "dark", "3d"} <= set(styles)
