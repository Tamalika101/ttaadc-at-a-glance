/* TTAADC at a Glance: renders every section from ./data/*.json */
(() => {
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const $ = (id) => document.getElementById(id);
  const fmt = (n) => (n == null ? "–" : Math.round(n).toLocaleString("en-IN"));
  const pct = (x, d = 0) => (x == null ? "–" : `${(x * 100).toFixed(d)}%`);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const PARTY = { TMP: "#2a78d6", BJP: "#eb6834" };
  const PARTY_NAME = { TMP: "Tipra Motha Party", BJP: "BJP" };
  const OTHER = "#8a8983";
  const AREA = { council: "#2a78d6", outside: "#8a8983", split: "#1baf7a" };
  const BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"];

  const layout = (extra = {}) => ({
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: "Inter, system-ui, sans-serif", size: 13, color: css("--ink-2") },
    margin: { l: 70, r: 30, t: 10, b: 50 },
    xaxis: { gridcolor: css("--rule"), zeroline: false, automargin: true },
    yaxis: { gridcolor: css("--rule"), zeroline: false, automargin: true },
    hoverlabel: { bgcolor: css("--surface"), bordercolor: css("--rule"), font: { color: css("--ink") } },
    showlegend: false, ...extra,
  });
  const cfg = { displayModeBar: false, responsive: true };
  const load = (n) => fetch(`data/${n}.json`, { cache: "no-cache" }).then((r) => {
    if (!r.ok) throw new Error(`${n}.json: ${r.status}`);
    return r.json();
  });

  const table = (head, rows, numCols = []) => `<table><thead><tr>${head.map((h, i) =>
    `<th class="${numCols.includes(i) ? "num" : ""}">${h}</th>`).join("")}</tr></thead><tbody>${rows.map((r) =>
    `<tr>${r.map((v, i) => `<td class="${numCols.includes(i) ? "num" : ""}">${v}</td>`).join("")}</tr>`).join("")}</tbody></table>`;

  Promise.all(["meta", "election", "water"].map(load))
    .then(([meta, el, w]) => {
      hero(meta, el, w);
      electionSection(el);
      waterSection(w);
      load("water_villages").then(villageSearch);
    })
    .catch((e) => document.querySelector("main").insertAdjacentHTML("afterbegin",
      `<p class="error">Could not load the data (${esc(e.message)}).</p>`));

  function hero(meta, el, w) {
    const c = w.by_area.council, o = w.by_area.outside;
    $("hero-stats").innerHTML = [
      [`${el.summary.won.TMP || 0} of ${el.summary.seats_total}`, "seats won by Tipra Motha Party in April 2026"],
      [pct(c.coverage), "of homes in council villages have a tap"],
      [pct(o.coverage), "in villages outside the council area"],
      [fmt(c.without_tap), "council-village homes still without a tap"],
    ].map(([b, s]) => `<div class="stat"><b>${b}</b><span>${s}</span></div>`).join("");
    $("updated").textContent = `Water data reported till ${w.reported_till || "–"} · election results declared 17 Apr 2026 · page rebuilt ${new Date(meta.built_at).toLocaleDateString("en-GB", { dateStyle: "medium" })}`;
  }

  // ---------------------------------------------------------------- election
  function electionSection(el) {
    const s = el.summary, seats = el.seats;
    const tmpShare = el.parties.find((p) => p.party === "TMP")?.vote_share;
    $("election-lede").textContent = `Voting took place on 12 April 2026 across 28 elected seats, 25 of them reserved for Scheduled Tribes. Tipra Motha Party won ${s.won.TMP} seats and the BJP ${s.won.BJP}. No other party won a seat.`;

    const parties = el.parties.slice().reverse();
    $("votes-text").textContent = `Seats tell only part of the story. Tipra Motha won ${pct(s.won.TMP / s.seats_total)} of seats on ${pct(tmpShare)} of the votes cast for the five main parties.`;
    Plotly.newPlot("chart-votes", [{
      type: "bar", orientation: "h", y: parties.map((p) => `${p.party} · ${p.seats_won} seat${p.seats_won === 1 ? "" : "s"}`),
      x: parties.map((p) => p.vote_share), marker: { color: parties.map((p) => PARTY[p.party] || OTHER) },
      text: parties.map((p) => pct(p.vote_share)), textposition: "outside", cliponaxis: false,
      customdata: parties.map((p) => [p.party_name, fmt(p.votes)]),
      hovertemplate: "%{customdata[0]}<br>%{customdata[1]} votes (%{x:.1%})<extra></extra>",
    }], layout({ xaxis: { tickformat: ".0%", gridcolor: css("--rule"), range: [0, 0.7] }, bargap: 0.35, margin: { l: 110, r: 40, t: 10, b: 40 } }), cfg);

    const sorted = seats.slice().sort((a, b) => a.margin_pct - b.margin_pct);
    $("margin-text").textContent = `Each bar is one constituency: the winner's lead over the runner-up, in percentage points of the vote. Half the seats were won by more than ${s.median_margin_pct.toFixed(0)} points. In ${s.landslides} seats the winner took three-quarters or more of the vote. At the other end, ${s.close_seats.length} seats were decided by under 5 points.`;
    Plotly.newPlot("chart-margins", [{
      type: "bar", orientation: "h", y: sorted.map((d) => `${d.no}. ${d.constituency}`), x: sorted.map((d) => d.margin_pct),
      marker: { color: sorted.map((d) => PARTY[d.winner_party]) },
      customdata: sorted.map((d) => [d.winner, d.winner_party, fmt(d.winner_votes), d.runner_up, d.runner_up_party, fmt(d.runner_up_votes), fmt(d.margin)]),
      hovertemplate: "<b>%{y}</b><br>%{customdata[0]} (%{customdata[1]}) %{customdata[2]}<br>%{customdata[3]} (%{customdata[4]}) %{customdata[5]}<br>Margin %{customdata[6]} votes, %{x:.1f} points<extra></extra>",
    }], layout({ xaxis: { title: "Winning margin (percentage points)", gridcolor: css("--rule") }, bargap: 0.25, margin: { l: 210, r: 30, t: 10, b: 50 } }), cfg);
    $("legend-margins").innerHTML = Object.entries(PARTY).map(([k, c]) => `<span><i style="background:${c}"></i>Won by ${PARTY_NAME[k]}</span>`).join("");

    $("close-table").innerHTML = table(["Constituency", "Winner", "Runner-up", "Margin (votes)", "Margin (points)"],
      sorted.filter((d) => d.margin_pct < 5).map((d) => [`${d.no}. ${esc(d.constituency)}`, `${esc(d.winner)} (${d.winner_party})`,
        `${esc(d.runner_up)} (${d.runner_up_party})`, fmt(d.margin), d.margin_pct.toFixed(1)]), [3, 4]);
    $("results-table").innerHTML = table(["#", "Constituency", "Winner", "Votes", "Share", "Runner-up", "Votes", "Margin"],
      seats.map((d) => [d.no, esc(d.constituency) + (d.reserved_st === "yes" ? ' <span class="pill">ST</span>' : ""),
        `${esc(d.winner)} (${d.winner_party})`, fmt(d.winner_votes), `${d.winner_pct.toFixed(1)}%`,
        `${esc(d.runner_up)} (${d.runner_up_party})`, fmt(d.runner_up_votes), fmt(d.margin)]), [0, 3, 4, 6, 7]);
  }

  // ---------------------------------------------------------------- water
  function waterSection(w) {
    const c = w.by_area.council, o = w.by_area.outside, sp = w.by_area.split;
    const gapPts = ((o.coverage - c.coverage) * 100).toFixed(1);
    $("water-gap").innerHTML = [
      [pct(c.coverage, 1), `Wholly council villages (${fmt(c.villages)} villages, ${fmt(c.households)} homes)`, "hl"],
      [pct(o.coverage, 1), `Villages outside the council area (${fmt(o.villages)})`],
      [pct(sp.coverage, 1), `Split villages, partly in the council area (${fmt(sp.villages)})`],
    ].map(([b, s, k]) => `<div class="stat ${k || ""}"><b>${b}</b><span>${s}</span></div>`).join("");
    $("water-gap-text").textContent = `Homes in the council's own villages are ${gapPts} points less likely to have a household tap than homes in villages outside it. That leaves ${fmt(c.without_tap)} council-village homes without one. ${c.villages_below_50} council villages are below 50% coverage, against ${o.villages_below_50} outside.`;

    const d = w.distribution;
    const share = (arr) => { const t = arr.reduce((a, b) => a + b, 0); return arr.map((x) => x / t); };
    $("dist-text").textContent = `Share of villages in each coverage band. Council villages are more spread out: fewer have reached 100%, and more sit in the lower bands.`;
    Plotly.newPlot("chart-dist", ["council", "outside"].map((a) => ({
      type: "bar", name: a === "council" ? "Council villages" : "Outside the council area", x: d.bins, y: share(d[a]),
      marker: { color: AREA[a], line: { color: css("--surface"), width: 2 } }, customdata: d[a],
      hovertemplate: `%{x}: %{y:.0%} of villages (%{customdata})<extra>${a === "council" ? "Council" : "Outside"}</extra>`,
    })), layout({ barmode: "group", showlegend: true, legend: { orientation: "h", y: -0.32 },
      yaxis: { tickformat: ".0%", title: "Share of villages", gridcolor: css("--rule") },
      xaxis: { title: { text: "Household tap coverage", standoff: 8 } }, bargap: 0.25, margin: { l: 70, r: 20, t: 10, b: 100 } }), cfg);

    const z = w.zones.slice().reverse();
    const lo = w.zones[0], hi = w.zones[w.zones.length - 1];
    $("zones-text").textContent = `Each bar is one of the council's zones (Block Advisory Committees), counting only villages wholly in the council area. Coverage ranges from ${pct(lo.coverage)} in ${lo.zone} to ${pct(hi.coverage)} in ${hi.zone}. Zones with only a few such villages are marked; their figures move a lot with one village.`;
    Plotly.newPlot("chart-zones", [{
      type: "bar", orientation: "h", y: z.map((r) => `${r.zone}${r.villages < 4 ? " *" : ""}`), x: z.map((r) => r.coverage),
      marker: { color: z.map((r) => (r.villages < 4 ? BLUE[1] : BLUE[4])) },
      customdata: z.map((r) => [r.district, r.villages, fmt(r.households), fmt(r.without_tap)]),
      hovertemplate: "<b>%{y}</b> (%{customdata[0]})<br>%{x:.1%} of %{customdata[2]} homes<br>%{customdata[1]} villages · %{customdata[3]} without a tap<extra></extra>",
    }], layout({ xaxis: { tickformat: ".0%", range: [0, 1.02], title: "Homes with a household tap", gridcolor: css("--rule") }, bargap: 0.2,
      margin: { l: 150, r: 30, t: 10, b: 50 },
      shapes: [{ type: "line", x0: o.coverage, x1: o.coverage, yref: "paper", y0: 0, y1: 1, line: { color: css("--ink-3"), dash: "dot", width: 1.5 } }],
      annotations: [{ x: o.coverage, yref: "paper", y: 1.01, text: `Outside the council: ${pct(o.coverage)}`, showarrow: false, font: { size: 11, color: css("--ink-3") }, xanchor: "right" }] }), cfg);

    const ds = w.districts.filter((r) => r.council != null && r.outside != null);
    const behindAll = ds.filter((r) => r.council < r.outside).length;
    $("districts-h").textContent = behindAll === ds.length ? "The gap appears in every district" : `The gap appears in ${behindAll} of ${ds.length} districts`;
    $("districts-text").textContent = `In ${behindAll} of Tripura's ${ds.length} districts, council villages have lower tap coverage than the district's other villages.`;
    Plotly.newPlot("chart-districts", ["council", "outside"].map((a) => ({
      type: "bar", name: a === "council" ? "Council villages" : "Outside the council area", x: ds.map((r) => r.district), y: ds.map((r) => r[a]),
      marker: { color: AREA[a], line: { color: css("--surface"), width: 2 } },
      hovertemplate: `%{x}: %{y:.1%}<extra>${a === "council" ? "Council" : "Outside"}</extra>`,
    })), layout({ barmode: "group", showlegend: true, legend: { orientation: "h", y: -0.25 },
      yaxis: { tickformat: ".0%", range: [0.5, 1], title: "Homes with a tap", gridcolor: css("--rule") }, bargap: 0.25, margin: { l: 70, r: 20, t: 10, b: 90 } }), cfg);

    $("behind-table").innerHTML = table(["Village", "Zone", "District", "Homes", "With a tap", "Coverage"],
      w.furthest_behind.map((r) => [esc(r.village), esc(r.zone || "–"), esc(r.district), fmt(r.households), fmt(r.connections), pct(r.coverage)]), [3, 4, 5]);
  }

  function villageSearch(rows) {
    const label = { council: "Council", split: "Split" };
    const input = $("village-input");
    input.addEventListener("input", () => {
      const q = input.value.trim().toLowerCase();
      if (q.length < 2) { $("village-result").innerHTML = ""; return; }
      const hits = rows.filter((r) => r.v.toLowerCase().includes(q)).slice(0, 12);
      $("village-result").innerHTML = hits.length ? table(["Village", "Area", "Zone", "District", "Homes", "Coverage"],
        hits.map((r) => [esc(r.v), label[r.a], esc(r.z || "–"), esc(r.d), fmt(r.h), pct(r.h ? r.c / r.h : null)]), [4, 5])
        : "<p>No village in the council area matches that name.</p>";
    });
  }
})();
