let all = [];

async function load() {
  const data = await fetch("/api/challenges").then((r) => r.json());
  all = data.items || [];
  document.getElementById("assetLink").href = data.asset_health_url || "#";
  const depts = new Set(all.map((c) => c.department));
  document.getElementById("stats").innerHTML = [
    ["Challenges", all.length],
    ["Departments", depts.size],
    ["Live demos", all.filter((c) => c.status === "live_demo").length],
  ]
    .map(([k, v]) => `<div class="stat"><strong>${v}</strong><span>${k}</span></div>`)
    .join("");
  render("");
}

function render(dept) {
  const items = dept ? all.filter((c) => c.department === dept) : all;
  document.getElementById("grid").innerHTML = items
    .map(
      (c) => `
    <a class="card" href="/challenge/${c.id}">
      <div class="num">Challenge ${String(c.id).padStart(2, "0")} · ${c.department}</div>
      <h3>${c.title}</h3>
      <p>${c.one_liner}</p>
      <span class="tag">${c.product_type}</span>
    </a>`
    )
    .join("");
}

document.querySelectorAll(".chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".chip").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    render(btn.dataset.dept || "");
  });
});

load().catch((err) => {
  document.getElementById("grid").innerHTML = `<p class="meta">${err}</p>`;
});
