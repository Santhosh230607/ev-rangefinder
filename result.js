/* ============================================
   Result page — render prediction + nearby stations
   ============================================ */

(function renderPrediction() {
  const raw = localStorage.getItem("ev_last_result");
  const startPlace = localStorage.getItem("ev_start_place") || "your location";
  document.getElementById("start-place").textContent = startPlace;

  if (!raw) {
    document.getElementById("range-km").textContent = "0";
    return;
  }

  const result = JSON.parse(raw);
  document.getElementById("range-km").textContent = result.range;

  const list = document.getElementById("factor-list");
  list.innerHTML = "";
  (result.factors || []).forEach((f) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${f.label}</span><span class="impact-${f.type === "pos" ? "pos" : "neg"}">${f.impact}</span>`;
    list.appendChild(li);
  });
})();

async function loadStations() {
  const stationList = document.getElementById("station-list");
  const startPlace = localStorage.getItem("ev_start_place") || "";

  try {
    const res = await fetch(API_BASE + "/nearest-stations?place=" + encodeURIComponent(startPlace));
    if (!res.ok) throw new Error("Station lookup failed");
    const stations = await res.json(); // [{ name, distance_km, address }]

    if (!stations.length) {
      stationList.innerHTML = '<li class="station-item"><span>No charging stations found nearby.</span></li>';
      return;
    }

    stationList.innerHTML = "";
    stations.forEach((s) => {
      const li = document.createElement("li");
      li.className = "station-item";
      li.innerHTML = `<span><strong>${s.name}</strong><br><span style="color:var(--text-muted);font-size:0.85rem;">${s.address || ""}</span></span><span class="distance">${s.distance_km.toFixed(1)} km</span>`;
      stationList.appendChild(li);
    });
  } catch (err) {
    console.warn("Backend unreachable — showing placeholder station data.", err);
    stationList.innerHTML = `
      <li class="station-item"><span><strong>Backend not connected</strong><br><span style="color:var(--text-muted);font-size:0.85rem;">Start app.py to see live nearby stations from OpenStreetMap.</span></span></li>
    `;
  }
}

loadStations();
