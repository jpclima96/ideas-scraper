const FILTER_GROUPS = [
  { key: "type", label: "Tipo" },
  { key: "source", label: "Fonte" },
  { key: "platform", label: "Plataforma" },
  { key: "styles", label: "Estilo" },
];
const SECONDARY = ["source", "platform", "styles"];
const CF_MAX = 60; // limite de slides na vitrine (a grade mostra tudo)

const state = { refs: [], dataBase: "", query: "", view: "stage", filtered: [], active: {} };
FILTER_GROUPS.forEach((g) => (state.active[g.key] = new Set()));

let swiper = null;
let backdropLayer = 0;
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ---------- Dados ---------- */
async function loadData() {
  for (const base of ["data/", "../data/"]) {
    try {
      const resp = await fetch(base + "references.json");
      if (resp.ok) return { base, refs: await resp.json() };
    } catch (_) { /* tenta o próximo caminho */ }
  }
  return { base: "", refs: [] };
}

function valuesOf(ref, key) {
  const v = ref[key];
  return Array.isArray(v) ? v : v ? [v] : [];
}

function visibleRefs() {
  const q = state.query.trim().toLowerCase();
  return state.refs.filter((ref) => {
    for (const g of FILTER_GROUPS) {
      const active = state.active[g.key];
      if (active.size && !valuesOf(ref, g.key).some((v) => active.has(v))) return false;
    }
    if (!q) return true;
    const hay = [ref.title, ref.author, ...(ref.tags || [])].join(" ").toLowerCase();
    return hay.includes(q);
  });
}

function badgeValues(ref) {
  return [ref.platform, ref.type, ...(ref.styles || [])].filter(
    (v) => v && v !== "unknown" && v !== "other"
  );
}

function countValues(key) {
  const counts = new Map();
  for (const ref of state.refs) {
    for (const v of valuesOf(ref, key)) counts.set(v, (counts.get(v) || 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

/* ---------- Backdrop imersivo ---------- */
function setBackdrop(url) {
  const layers = document.querySelectorAll(".backdrop-layer");
  if (!layers.length) return;
  const next = layers[backdropLayer ^ 1];
  const cur = layers[backdropLayer];
  next.style.backgroundImage = url ? `url("${url}")` : "none";
  next.classList.add("show");
  cur.classList.remove("show");
  backdropLayer ^= 1;
}

/* ---------- Filtros ---------- */
function chip(label, n, on, handler) {
  const b = document.createElement("button");
  b.className = "chip" + (on ? " on" : "");
  b.innerHTML = n == null ? label : `${label}<span class="n">${n}</span>`;
  b.onclick = handler;
  return b;
}

function renderChips() {
  const root = document.getElementById("chips");
  root.innerHTML = "";
  root.appendChild(
    chip("Todos", null, state.active.type.size === 0, () => {
      state.active.type.clear();
      onFilterChange();
    })
  );
  for (const [value, n] of countValues("type")) {
    root.appendChild(
      chip(value, n, state.active.type.has(value), () => {
        toggle("type", value);
      })
    );
  }
}

function renderFilterPanel() {
  const panel = document.getElementById("filter-panel");
  panel.innerHTML = "";
  for (const key of SECONDARY) {
    const entries = countValues(key);
    if (!entries.length) continue;
    const group = document.createElement("div");
    group.className = "fp-group";
    const label = document.createElement("div");
    label.className = "fp-label";
    label.textContent = FILTER_GROUPS.find((g) => g.key === key).label;
    const chips = document.createElement("div");
    chips.className = "fp-chips";
    for (const [value, n] of entries) {
      chips.appendChild(chip(value, n, state.active[key].has(value), () => toggle(key, value)));
    }
    group.append(label, chips);
    panel.appendChild(group);
  }
  const footer = document.createElement("div");
  footer.className = "fp-footer";
  const clear = document.createElement("button");
  clear.className = "fp-clear";
  clear.textContent = "Limpar filtros";
  clear.onclick = () => {
    SECONDARY.forEach((k) => state.active[k].clear());
    onFilterChange();
  };
  footer.appendChild(clear);
  panel.appendChild(footer);

  const activeCount = SECONDARY.reduce((s, k) => s + state.active[k].size, 0);
  const badge = document.getElementById("filters-badge");
  badge.hidden = activeCount === 0;
  badge.textContent = String(activeCount);
}

function toggle(key, value) {
  const set = state.active[key];
  set.has(value) ? set.delete(value) : set.add(value);
  onFilterChange();
}

/* ---------- Coverflow ---------- */
function buildSlides() {
  const wrapper = document.getElementById("cf-wrapper");
  wrapper.innerHTML = "";
  for (const ref of state.filtered.slice(0, CF_MAX)) {
    const slide = document.createElement("div");
    slide.className = "swiper-slide";
    if (ref.thumb) {
      const img = document.createElement("img");
      img.loading = "lazy";
      img.src = state.dataBase + ref.thumb;
      img.alt = ref.title;
      slide.appendChild(img);
    } else {
      slide.innerHTML = '<div class="noimg">🖼️</div>';
    }
    slide.addEventListener("click", () => {
      if (swiper && slide === swiper.slides[swiper.activeIndex]) {
        window.open(ref.url, "_blank", "noopener");
      }
    });
    wrapper.appendChild(slide);
  }
}

function initSwiper() {
  const items = state.filtered.slice(0, CF_MAX);
  const middle = items.length ? Math.floor((items.length - 1) / 2) : 0;
  swiper = new Swiper(".swiper.cf", {
    effect: reduceMotion ? "slide" : "coverflow",
    grabCursor: true,
    centeredSlides: true,
    slidesPerView: "auto",
    initialSlide: middle,
    speed: reduceMotion ? 200 : 450,
    keyboard: { enabled: true },
    navigation: { prevEl: ".cf-prev", nextEl: ".cf-next" },
    coverflowEffect: { rotate: 8, depth: 220, modifier: 1.6, stretch: 0, slideShadows: true },
    on: {
      init(sw) { updateCoverMeta(sw); },
      slideChange(sw) { updateCoverMeta(sw); },
    },
  });
}

function updateCoverMeta(sw) {
  const inst = sw || swiper;
  const meta = document.getElementById("cf-meta");
  const counter = document.getElementById("cf-counter");
  const items = state.filtered.slice(0, CF_MAX);
  const idx = inst ? inst.activeIndex : 0;
  const ref = items[idx];
  if (!ref) { meta.innerHTML = ""; counter.textContent = ""; setBackdrop(null); return; }

  const badges = badgeValues(ref).map((v) => `<span class="badge">${v}</span>`).join("");
  meta.innerHTML =
    `<div class="cf-title">${ref.title}</div>` +
    `<div class="cf-byline">${[ref.author, ref.source].filter(Boolean).join(" · ")}</div>` +
    `<div class="cf-badges">${badges}</div>` +
    `<a class="cf-link" href="${ref.url}" target="_blank" rel="noopener noreferrer">ver original ↗</a>`;

  const extra = state.filtered.length > items.length ? ` de ${state.filtered.length}` : "";
  counter.textContent = `${idx + 1} / ${items.length}${extra}`;
  setBackdrop(ref.thumb ? state.dataBase + ref.thumb : null);
}

function rebuildStage() {
  if (swiper) { swiper.destroy(true, true); swiper = null; }
  buildSlides();
  initSwiper();
}

/* ---------- Grade ---------- */
function renderGrid() {
  const grid = document.getElementById("grid");
  grid.innerHTML = "";
  document.getElementById("count").textContent =
    `${state.filtered.length} de ${state.refs.length} referências`;

  for (const ref of state.filtered) {
    const card = document.createElement("a");
    card.className = "card";
    card.href = ref.url;
    card.target = "_blank";
    card.rel = "noopener noreferrer";

    const imgWrap = document.createElement("div");
    imgWrap.className = "img-wrap";
    if (ref.thumb) {
      const img = document.createElement("img");
      img.loading = "lazy";
      img.src = state.dataBase + ref.thumb;
      img.alt = ref.title;
      imgWrap.appendChild(img);
    } else {
      imgWrap.innerHTML = '<div class="noimg">🖼️</div>';
    }

    const meta = document.createElement("div");
    meta.className = "meta";
    const title = document.createElement("div");
    title.className = "title";
    title.textContent = ref.title;
    const byline = document.createElement("div");
    byline.className = "byline";
    byline.textContent = [ref.author, ref.source].filter(Boolean).join(" · ");
    const badges = document.createElement("div");
    badges.className = "badges";
    for (const v of badgeValues(ref)) {
      const b = document.createElement("span");
      b.className = "badge";
      b.textContent = v;
      badges.appendChild(b);
    }
    meta.append(title, byline, badges);
    card.append(imgWrap, meta);
    grid.appendChild(card);
  }
}

/* ---------- Visões ---------- */
function applyView() {
  const isStage = state.view === "stage";
  const empty = state.filtered.length === 0;
  document.getElementById("stage-view").hidden = false; // hero/controles sempre visíveis
  document.querySelector(".coverflow").hidden = empty || !isStage;
  document.querySelector(".cf-info").hidden = empty || !isStage;
  document.getElementById("grid-view").hidden = empty || isStage;
  document.getElementById("empty").hidden = !empty;
  document.querySelectorAll("#view-toggle button").forEach((b) => {
    const on = b.dataset.view === state.view;
    b.classList.toggle("on", on);
    b.setAttribute("aria-selected", String(on));
  });
  if (isStage && swiper) swiper.update();
}

function render() {
  state.filtered = visibleRefs();
  renderChips();
  renderFilterPanel();
  rebuildStage();
  renderGrid();
  applyView();
}

function onFilterChange() {
  render();
}

/* ---------- Eventos ---------- */
document.getElementById("search").addEventListener("input", (e) => {
  state.query = e.target.value;
  onFilterChange();
});

document.getElementById("view-toggle").addEventListener("click", (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  state.view = btn.dataset.view;
  applyView();
});

// Painel de filtros: abrir/fechar
const filtersBtn = document.getElementById("filters-btn");
const filterPanel = document.getElementById("filter-panel");
filtersBtn.addEventListener("click", () => {
  const open = filterPanel.hidden;
  filterPanel.hidden = !open;
  filtersBtn.setAttribute("aria-expanded", String(open));
});
document.addEventListener("click", (e) => {
  if (!filterPanel.hidden && !e.target.closest(".filters-anchor")) {
    filterPanel.hidden = true;
    filtersBtn.setAttribute("aria-expanded", "false");
  }
});

loadData().then(({ base, refs }) => {
  state.dataBase = base;
  state.refs = refs;
  render();
});
