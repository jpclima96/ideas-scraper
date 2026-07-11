# ideas-scraper 💡

Acervo pessoal e automatizado de referências de design **web & mobile**. Uma GitHub Action diária coleta novidades do **Dribbble** (RSS), **Land-book** (HTML) e **Behance** (Playwright), categoriza por plataforma/tipo/estilo e publica uma **galeria com filtros no GitHub Pages**.

As imagens salvas são apenas miniaturas (~400px, webp) com link e crédito aos autores originais.

## Como funciona

```
GitHub Action (cron diário)
  → python -m scraper.main   # coleta, deduplica, gera thumbs, categoriza
  → commit de data/          # references.json + thumbs/*.webp
  → deploy no GitHub Pages   # site/ + data/ viram a galeria
```

- `scraper/sources/` — um coletor por fonte; falha em uma fonte não derruba as outras.
- `scraper/categorize.py` — taxonomia por palavras-chave sobre título + tags da fonte.
- `data/references.json` — fonte de verdade do acervo (dedup por hash da URL).
- `site/` — galeria estática (HTML/CSS/JS puro): filtros por fonte, plataforma, tipo e estilo + busca.

## Rodando localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium   # só necessário para o coletor do Behance

python -m scraper.main   # coleta e atualiza data/
pytest                   # testes

python -m http.server    # abrir http://localhost:8000/site/
```

## Ativação (uma vez)

1. Em **Settings → Pages**, defina o source como **GitHub Actions**.
2. Rode o workflow **"Coletar referências e publicar galeria"** manualmente (aba Actions → Run workflow) ou aguarde o cron diário (08:00 UTC).

## Planejamento e extensões futuras

Ver [PLANO.md](PLANO.md) — inclui digest por e-mail, categorização com Claude API e filtro por paleta de cores como próximos passos possíveis.
