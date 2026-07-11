from . import arena, behance, dribbble, landbook

# Fonte ativa: Are.na (API pública, sem anti-bot). Dribbble, Land-book e
# Behance ficam desativados porque bloqueiam scraping (403/202/anti-bot) —
# os módulos seguem no repo para reativação futura ou "adicionar manualmente".
ACTIVE_SOURCES = {
    "arena": arena.fetch,
}

# Desativadas (bloqueadas por anti-bot em 2026-07):
_DISABLED_SOURCES = {
    "dribbble": dribbble.fetch,
    "landbook": landbook.fetch,
    "behance": behance.fetch,
}
