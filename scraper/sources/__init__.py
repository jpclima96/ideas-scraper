from . import behance, dribbble, landbook

ACTIVE_SOURCES = {
    "dribbble": dribbble.fetch,
    "landbook": landbook.fetch,
    "behance": behance.fetch,
}
