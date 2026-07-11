"""Categorização por palavras-chave sobre título + tags da fonte."""
from __future__ import annotations

import re

PLATFORM_KEYWORDS = {
    "mobile": ["mobile", "ios", "android", "iphone", "smartwatch", "watch", "tablet", "app"],
    "web": [
        "web", "website", "web design", "webdesign", "landing", "landing page",
        "desktop", "dashboard", "saas", "homepage", "hero", "portfolio",
    ],
}

# Ordem importa: o primeiro tipo que casar vence, do mais específico ao mais genérico.
TYPE_KEYWORDS = {
    "dashboard": ["dashboard", "admin", "analytics", "crm", "statistics", "saas app", "fintech app"],
    "ecommerce": ["ecommerce", "e-commerce", "shop", "store", "checkout", "cart", "product page"],
    "portfolio": ["portfolio", "agency", "studio site"],
    "landing": ["landing", "landing page", "homepage", "home page", "hero", "onepage", "marketing site", "website"],
    "app": ["app", "mobile", "ios", "android"],
}

STYLE_KEYWORDS = {
    "dark": ["dark", "dark mode", "black"],
    "minimal": ["minimal", "minimalist", "clean", "simple"],
    "3d": ["3d", "blender", "render", "isometric"],
    "gradient": ["gradient"],
    "glassmorphism": ["glassmorphism", "glass", "frosted"],
    "brutalist": ["brutalist", "brutalism"],
    "illustration": ["illustration", "illustrated", "cartoon"],
    "retro": ["retro", "vintage", "y2k"],
    "typography": ["typography", "lettering", "typographic"],
    "animation": ["animation", "motion", "interaction", "micro-interaction"],
}


def _matches(haystack: str, keyword: str) -> bool:
    # Casa palavras inteiras para evitar falsos positivos ("app" em "happy").
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", haystack) is not None


def categorize(title: str, tags: list[str]) -> tuple[str, str, list[str]]:
    """Retorna (platform, type, styles) para um item."""
    haystack = " ".join([title, *tags]).lower()

    platform = "unknown"
    for name, keywords in PLATFORM_KEYWORDS.items():
        if any(_matches(haystack, kw) for kw in keywords):
            platform = name
            break

    type_ = "other"
    for name, keywords in TYPE_KEYWORDS.items():
        if any(_matches(haystack, kw) for kw in keywords):
            type_ = name
            break
    if type_ == "other" and platform == "mobile":
        type_ = "app"

    styles = [
        name
        for name, keywords in STYLE_KEYWORDS.items()
        if any(_matches(haystack, kw) for kw in keywords)
    ]
    return platform, type_, styles
