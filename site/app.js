const FILTER_GROUPS = [
  { key: "type", label: "Tipo" },
  { key: "source", label: "Fonte" },
  { key: "platform", label: "Plataforma" },
  { key: "styles", label: "Estilo" },
];
const CF_MAX = 60; // limite de cards na vitrine (a grade mostra tudo)

const state = { refs: [], dataBase: "", query: "", view: "coverflow", focus: 0, filtered: [], active: {} };
FILTER_GROUPS.forEach((g) => (state.active[g.key] = new Set()));

let cfCards = [];
let suppressClick = false; // evita que um swipe dispare o clique do card

// No Pages o artefato tem data/ ao lado do index; rodando do repo, data/ é irmã de site/.
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

/* ---------- Filtros ---------- */
function renderFilters() {
  const root = document.getElementById("filters");
  root.innerHTML = "";
  for (const group of FILTER_GROUPS) {
    const counts = new Map();
    for (const ref of state.refs) {
      for (const v of valuesOf(ref, group.key)) counts.set(v, (counts.get(v) || 0) + 1);
    }
    if (!counts.size) continue;

    const primary = group.key === "type";
    const row = document.createElement("div");
    row.className = "filter-row" + (primary ? "" : " secondary");

    if (!primary) {
      const label = document.createElement("span");
      label.className = "filter-label";
      label.textContent = group.label;
      row.appendChild(label);
    } else {
      const all = document.createElement("button");
      all.className = "chip" + (state.active.type.size === 0 ? " on" : "");
      all.textContent = "Todos";
      all.onclick = () => { state.active.type.clear(); onFilterChange(); };
      row.appendChild(all);
    }

    [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .forEach(([value, n]) => {
        const chip = document.createElement("button");
        chip.className = "chip" + (state.active[group.key].has(value) ? " on" : "");
        chip.innerHTML = `${value}<span class="n">${n}</span>`;
        chip.onclick = () => {
          const set = state.active[group.key];
          set.has(value) ? set.delete(value) : set.add(value);
          onFilterChange();
        };
        row.appendChild(chip);
      });
    root.appendChild(row);
  }
}

/* ---------- Coverflow ---------- */
function renderCoverflow() {
  const stage = document.getElementById("cf-stage");
  stage.innerHTML = "";
  cfCards = [];
  const items = state.filtered.slice(0, CF_MAX);

  items.forEach((ref, i) => {
    const card = document.createElement("div");
    card.className = "cf-card";
    if (ref.thumb) {
      const img = document.createElement("img");
      img.loading = "lazy";
      img.src = state.dataBase + ref.thumb;
      img.alt = ref.title;
      card.appendChild(img);
    } else {
      card.innerHTML = '<div class="noimg">🖼️</div>';
    }
    card.addEventListener("click", () => {
      if (suppressClick) return;
      if (i === state.focus) window.open(ref.url, "_blank", "noopener");
      else { state.focus = i; positionCoverflow(); }
    });
    stage.appendChild(card);
    cfCards.push(card);
  });
  positionCoverflow();
}

function positionCoverflow() {
  const spacing = 150, angle = 12, depth = 120;
  cfCards.forEach((card, i) => {
    const off = i - state.focus;
    const abs = Math.abs(off);
    if (abs > 4) {
      card.style.opacity = "0";
      card.style.pointerEvents = "none";
      card.style.transform = `translateX(${off * spacing}px) translateZ(-700px)`;
      return;
    }
    const scale = off === 0 ? 1 : Math.max(0.62, 1 - abs * 0.12);
    card.style.transform =
      `translateX(${off * spacing}px) translateZ(${-abs * depth}px) rotateY(${off * -angle}deg) scale(${scale})`;
    card.style.opacity = String(1 - abs * 0.14);
    card.style.zIndex = String(50 - abs);
    card.style.pointerEvents = "auto";
    card.classList.toggle("focused", off === 0);
  });
  updateCoverMeta();
}

function updateCoverMeta() {
  const meta = document.getElementById("cf-meta");
  const counter = document.getElementById("cf-counter");
  const items = state.filtered.slice(0, CF_MAX);
  const ref = items[state.focus];
  if (!ref) { meta.innerHTML = ""; counter.textContent = ""; return; }

  const badges = badgeValues(ref)
    .map((v) => `<span class="badge">${v}</span>`)
    .join("");
  meta.innerHTML =
    `<div class="cf-title">${ref.title}</div>` +
    `<div class="cf-byline">${[ref.author, ref.source].filter(Boolean).join(" · ")}</div>` +
    `<div class="cf-badges">${badges}</div>` +
    `<a class="cf-link" href="${ref.url}" target="_blank" rel="noopener noreferrer">ver original ↗</a>`;

  const extra = state.filtered.length > items.length ? ` (de ${state.filtered.length})` : "";
  counter.textContent = `${state.focus + 1} / ${items.length}${extra}`;
}

function moveFocus(delta) {
  const max = Math.min(state.filtered.length, CF_MAX) - 1;
  state.focus = Math.max(0, Math.min(max, state.focus + delta));
  positionCoverflow();
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
  const isCover = state.view === "coverflow";
  const empty = state.filtered.length === 0;
  document.getElementById("coverflow").hidden = empty || !isCover;
  document.getElementById("grid-view").hidden = empty || isCover;
  document.getElementById("empty").hidden = !empty;
  document.querySelectorAll("#view-toggle button").forEach((b) => {
    const on = b.dataset.view === state.view;
    b.classList.toggle("on", on);
    b.setAttribute("aria-selected", String(on));
  });
}

// Foco central deixa a vitrine equilibrada (cards dos dois lados), como na referência.
function centerFocus() {
  const n = Math.min(state.filtered.length, CF_MAX);
  return n > 0 ? Math.floor((n - 1) / 2) : 0;
}

function render() {
  state.filtered = visibleRefs();
  const max = Math.min(state.filtered.length, CF_MAX) - 1;
  state.focus = Math.max(0, Math.min(max, state.focus));
  renderFilters();
  renderCoverflow();
  renderGrid();
  applyView();
}

function onFilterChange() {
  state.filtered = visibleRefs();
  state.focus = centerFocus();
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

document.querySelector(".cf-prev").addEventListener("click", () => moveFocus(-1));
document.querySelector(".cf-next").addEventListener("click", () => moveFocus(1));

document.addEventListener("keydown", (e) => {
  if (state.view !== "coverflow") return;
  if (e.key === "ArrowLeft") moveFocus(-1);
  else if (e.key === "ArrowRight") moveFocus(1);
});

// Arrasto / swipe no palco
(() => {
  const stage = document.getElementById("cf-stage");
  let startX = null;
  stage.addEventListener("pointerdown", (e) => { startX = e.clientX; suppressClick = false; });
  window.addEventListener("pointerup", (e) => {
    if (startX === null) return;
    const dx = e.clientX - startX;
    startX = null;
    if (Math.abs(dx) > 45) {
      suppressClick = true; // swipe reconhecido: não deixa o clique do card agir
      moveFocus(dx < 0 ? 1 : -1);
      setTimeout(() => { suppressClick = false; }, 0);
    }
  });
})();

loadData().then(({ base, refs }) => {
  state.dataBase = base;
  state.refs = refs;
  state.filtered = visibleRefs();
  state.focus = centerFocus();
  render();
});
