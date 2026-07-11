const FILTER_GROUPS = [
  { key: "source", label: "Fonte" },
  { key: "platform", label: "Plataforma" },
  { key: "type", label: "Tipo" },
  { key: "styles", label: "Estilo" },
];

const state = { refs: [], dataBase: "", query: "", active: {} };
FILTER_GROUPS.forEach((g) => (state.active[g.key] = new Set()));

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

function renderFilters() {
  const root = document.getElementById("filters");
  root.innerHTML = "";
  for (const group of FILTER_GROUPS) {
    const counts = new Map();
    for (const ref of state.refs) {
      for (const v of valuesOf(ref, group.key)) counts.set(v, (counts.get(v) || 0) + 1);
    }
    if (!counts.size) continue;
    const row = document.createElement("div");
    row.className = "filter-row";
    const label = document.createElement("span");
    label.className = "filter-label";
    label.textContent = group.label;
    row.appendChild(label);
    [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .forEach(([value, n]) => {
        const chip = document.createElement("button");
        chip.className = "chip" + (state.active[group.key].has(value) ? " on" : "");
        chip.innerHTML = `${value}<span class="n">${n}</span>`;
        chip.onclick = () => {
          const set = state.active[group.key];
          set.has(value) ? set.delete(value) : set.add(value);
          render();
        };
        row.appendChild(chip);
      });
    root.appendChild(row);
  }
}

function renderGrid() {
  const refs = visibleRefs();
  const grid = document.getElementById("grid");
  grid.innerHTML = "";
  document.getElementById("empty").hidden = refs.length > 0;
  document.getElementById("count").textContent =
    `${refs.length} de ${state.refs.length} referências`;

  for (const ref of refs) {
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
    for (const v of [ref.platform, ref.type, ...(ref.styles || [])]) {
      if (!v || v === "unknown" || v === "other") continue;
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

function render() {
  renderFilters();
  renderGrid();
}

document.getElementById("search").addEventListener("input", (e) => {
  state.query = e.target.value;
  renderGrid();
});

loadData().then(({ base, refs }) => {
  state.dataBase = base;
  state.refs = refs;
  render();
});
