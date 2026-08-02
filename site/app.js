// On GitHub Pages the JSON is copied into site/ alongside index.html.
// For local dev: run `python -m http.server 8000 --directory site` after
// copying data/internships.json into the site/ folder.
const DATA_URL = "internships.json";

const state = {
  internships: [],
  search: "",
  company: "",
  sort: "newest",
};

const el = {
  cards: document.getElementById("cards"),
  emptyState: document.getElementById("empty-state"),
  resultCount: document.getElementById("result-count"),
  lastUpdated: document.getElementById("last-updated"),
  search: document.getElementById("search"),
  companyFilter: document.getElementById("company-filter"),
  sortOrder: document.getElementById("sort-order"),
};

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function formatDate(iso) {
  if (!iso) return "Unknown date";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function populateCompanyFilter(internships) {
  const companies = [...new Set(internships.map((i) => i.company))].sort();
  for (const company of companies) {
    const opt = document.createElement("option");
    opt.value = company;
    opt.textContent = company;
    el.companyFilter.appendChild(opt);
  }
}

function applyFilters() {
  const q = state.search.trim().toLowerCase();
  let results = state.internships.filter((i) => {
    if (state.company && i.company !== state.company) return false;
    if (!q) return true;
    const haystack = `${i.title} ${i.company} ${i.location}`.toLowerCase();
    return haystack.includes(q);
  });

  results.sort((a, b) => {
    const cmp = (a.date_posted || "").localeCompare(b.date_posted || "");
    return state.sort === "newest" ? -cmp : cmp;
  });

  render(results);
}

function render(results) {
  el.cards.innerHTML = "";
  el.resultCount.textContent = `${results.length} listing${results.length === 1 ? "" : "s"} found`;
  el.emptyState.hidden = results.length !== 0;

  for (const item of results) {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <span class="company">${escapeHtml(item.company)}</span>
      <p class="title">${escapeHtml(item.title)}</p>
      <span class="location">${escapeHtml(item.location)}</span>
      <span class="date">Posted ${formatDate(item.date_posted)}</span>
      <a class="apply-btn" href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">Apply →</a>
    `;
    el.cards.appendChild(card);
  }
}

async function init() {
  try {
    const res = await fetch(DATA_URL, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.internships = data.internships || [];
    el.lastUpdated.textContent = data.last_updated
      ? `Last updated: ${new Date(data.last_updated).toLocaleString()}`
      : "Last updated: unknown";

    populateCompanyFilter(state.internships);
    applyFilters();
  } catch (err) {
    el.lastUpdated.textContent = "Failed to load internship data.";
    el.emptyState.textContent = `Could not load data/internships.json (${err.message}).`;
    el.emptyState.hidden = false;
  }
}

el.search.addEventListener("input", (e) => {
  state.search = e.target.value;
  applyFilters();
});
el.companyFilter.addEventListener("change", (e) => {
  state.company = e.target.value;
  applyFilters();
});
el.sortOrder.addEventListener("change", (e) => {
  state.sort = e.target.value;
  applyFilters();
});

init();
