# Plano — Scraper de Ideias de Design (Web & Mobile)

## 1. Objetivo

Coletar automaticamente referências de design (web e mobile) de fontes como Dribbble e Behance, salvá-las **categorizadas** (ex.: landing page, dashboard, app fintech, dark mode, etc.) e entregá-las de forma fácil de consultar durante os projetos.

## 2. Fontes de dados — realidade e estratégia

Ponto crítico do projeto: as duas fontes principais **não oferecem APIs públicas abertas**.

| Fonte | Situação | Estratégia recomendada |
|---|---|---|
| **Dribbble** | API v2 existe, mas só retorna shots do próprio usuário. Porém há **feeds RSS públicos** (`dribbble.com/shots/popular.rss`, por tag e por usuário) | Usar RSS como via principal; scraping HTML leve só como complemento |
| **Behance** | API oficial descontinuada pela Adobe (sem novas chaves) | Scraping com Playwright (páginas renderizam via JS). Respeitar rate limit baixo (1 req a cada 3–5s) |
| **Awwwards** | Sem API | Scraping HTML simples das páginas de nomeados/vencedores |
| **Land-book / SiteInspire / Godly** | Sem API, HTML estático simples | Scraping leve, ótimo custo-benefício para referências de landing pages |
| **Mobbin** | Melhor fonte para mobile, mas paga e sem API | Fora do escopo automatizado; citar como fonte manual |

Diretrizes: identificar-se via User-Agent, respeitar `robots.txt`, cachear tudo (nunca re-baixar), salvar apenas **thumbnail + link para a fonte original** (evita problema de direitos autorais — as imagens pertencem aos designers).

## 3. Arquitetura proposta

```
[GitHub Actions (cron diário/semanal)]
        │
        ▼
[Scraper - Python]
  ├── coletores por fonte (RSS + Playwright)
  ├── deduplicação (hash da URL)
  └── categorização
        │
        ▼
[data/references.json  +  data/thumbs/]  ← commitado no repo
        │
        ├──► [Landing page estática (GitHub Pages)] — galeria com filtros
        └──► [E-mail digest semanal] — top novidades da semana
```

### Componentes

1. **Coletores** (`scraper/sources/`): um módulo por fonte, todos retornando o mesmo formato:
   ```json
   {
     "id": "hash-da-url",
     "title": "Fintech Dashboard Dark",
     "source": "dribbble",
     "url": "https://dribbble.com/shots/...",
     "thumb": "data/thumbs/abc123.webp",
     "author": "nome do designer",
     "tags": ["dashboard", "fintech", "dark-mode"],
     "platform": "web",
     "collected_at": "2026-07-11"
   }
   ```
2. **Categorização** em duas camadas:
   - **Camada 1 (grátis):** tags que a própria fonte fornece + palavras-chave no título.
   - **Camada 2 (opcional):** Claude API (Haiku, barato) classifica cada item em uma taxonomia fixa — ex.: `plataforma` (web/mobile), `tipo` (landing, dashboard, app, e-commerce…), `estilo` (minimalista, brutalist, glassmorphism…), `setor` (fintech, saúde, SaaS…).
3. **Armazenamento:** JSON + thumbnails no próprio repo. Simples, versionado, sem custo. Se passar de ~1 GB de imagens, migrar thumbs para um bucket (R2/S3) — decisão futura, não bloqueia o MVP.

## 4. Decisão: repositório, landing page ou e-mail?

Os três não são excludentes — a pergunta certa é **qual é a base e o que vem por cima**.

| Opção | Prós | Contras |
|---|---|---|
| **Só repositório** | Zero custo, versionado, dados em JSON reutilizáveis | Navegar referências visuais em JSON/Markdown é ruim — design se consome com os olhos |
| **Só landing page** | Ótima experiência de consulta (galeria, filtros) | Precisa de onde guardar os dados de qualquer forma |
| **Só e-mail** | Chega até você sem esforço | Não serve como acervo pesquisável; e-mail antigo se perde |

### ✅ Recomendação: os três em camadas, nesta ordem

1. **Repositório como fonte de verdade** (obrigatório) — scraper + dados JSON + thumbs, rodando via GitHub Actions.
2. **Landing page estática no GitHub Pages** (o "produto") — galeria gerada a partir do JSON, com filtros por categoria/plataforma/estilo e busca. Custo zero, deploy automático no mesmo Action.
3. **E-mail digest semanal** (opcional, fase 3) — Action semanal envia as ~10 melhores novidades via [Resend](https://resend.com) (free tier: 100 emails/dia) ou SMTP do Gmail. Serve como *lembrete* para visitar a galeria, não como acervo.

Justificativa: o repo você precisa ter de qualquer jeito; a galeria é o que torna o acervo **utilizável** para buscar referência no meio de um projeto; o e-mail resolve o problema de "esquecer que a ferramenta existe".

## 5. Stack sugerida

- **Python 3.12** — `httpx` + `feedparser` (RSS), `playwright` (Behance/JS), `Pillow` (thumbs em webp)
- **Frontend:** HTML/CSS/JS puro ou Astro — página estática que lê o `references.json` (não precisa de framework pesado)
- **Automação:** GitHub Actions com cron (ex.: diário às 8h) + deploy do Pages
- **Categorização IA (opcional):** Claude Haiku via API — custo estimado < US$ 1/mês para centenas de itens

## 6. Fases de implementação

### Fase 1 — MVP (repo + 1 fonte)
- [ ] Estrutura do projeto Python
- [ ] Coletor Dribbble via RSS (popular + 3–4 tags de interesse)
- [ ] Deduplicação + download de thumbnails
- [ ] Categorização por tags/palavras-chave (sem IA)
- [ ] GitHub Action rodando diariamente e commitando `data/`

### Fase 2 — Galeria (GitHub Pages)
- [ ] Página de galeria com grid de thumbs
- [ ] Filtros: plataforma, tipo, estilo, fonte
- [ ] Busca por texto
- [ ] Deploy automático no mesmo workflow

### Fase 3 — Mais fontes + inteligência
- [ ] Coletor Behance (Playwright)
- [ ] Coletor Land-book / Awwwards
- [ ] Categorização com Claude API (taxonomia fixa)
- [ ] E-mail digest semanal

### Fase 4 — Refinamentos (conforme uso)
- [ ] Favoritos / coleções por projeto
- [ ] Detecção de paleta de cores das thumbs (filtrar por cor)
- [ ] Migrar thumbs para bucket se o repo crescer demais

## 7. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Fonte muda o HTML e quebra o scraper | Coletores isolados por fonte; falha em um não derruba os outros; Action alerta no log |
| Bloqueio por rate limit / anti-bot (Behance) | Priorizar RSS; scraping lento e educado; se bloquear, a fonte sai sem afetar o resto |
| Direitos autorais das imagens | Guardar só thumbnail + link e crédito ao autor; galeria é privada/pessoal |
| Repo inchar com imagens | Thumbs em webp ~30 KB; monitorar e migrar para bucket na Fase 4 |
