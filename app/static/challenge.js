const id = Number(location.pathname.split("/").pop());

function fmt(value) {
  if (value == null) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

async function boot() {
  const meta = await fetch(`/api/challenges/${id}`).then((r) => {
    if (!r.ok) throw new Error("Challenge not found");
    return r.json();
  });
  document.title = `${meta.title} · TISC`;
  document.getElementById("hero").innerHTML = `
    <p class="eyebrow">Challenge ${String(meta.id).padStart(2, "0")} · ${meta.department} · ${meta.product_type}</p>
    <h1>${meta.title}</h1>
    <p class="lede">${meta.one_liner}<br><strong style="color:var(--accent)">Impact:</strong> ${meta.impact}</p>`;

  const demo = await fetch(`/api/challenges/${id}/demo`).then((r) => {
    if (!r.ok) throw new Error("Demo failed");
    return r.json();
  });

  const summary = demo.summary || {};
  document.getElementById("kpis").innerHTML = Object.entries(summary)
    .filter(([, v]) => typeof v !== "object")
    .slice(0, 8)
    .map(([k, v]) => `<article class="kpi"><span>${k.replaceAll("_", " ")}</span><strong>${fmt(v)}</strong></article>`)
    .join("");

  document.getElementById("actions").innerHTML = (demo.actions || [])
    .map((a) => `<li>${typeof a === "string" ? a : a.title || JSON.stringify(a)}</li>`)
    .join("") || "<li>No actions</li>";

  const rows = demo.rows || [];
  if (!rows.length) {
    document.getElementById("thead").innerHTML = "";
    document.getElementById("tbody").innerHTML = "<tr><td>No rows</td></tr>";
  } else {
    const keys = Object.keys(rows[0]).slice(0, 8);
    document.getElementById("thead").innerHTML =
      `<tr>${keys.map((k) => `<th>${k}</th>`).join("")}</tr>`;
    document.getElementById("tbody").innerHTML = rows
      .slice(0, 80)
      .map((row) => `<tr>${keys.map((k) => `<td>${fmt(row[k])}</td>`).join("")}</tr>`)
      .join("");
  }

  if (summary.full_product_url) {
    document.getElementById("extra").innerHTML =
      `Full enterprise product for this challenge: <a href="${summary.full_product_url}" style="color:var(--accent)">${summary.full_product_url}</a>`;
  }
}

boot().catch((err) => {
  document.getElementById("hero").innerHTML = `<h1>Error</h1><p class="lede">${err.message || err}</p>`;
});
