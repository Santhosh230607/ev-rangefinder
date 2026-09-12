/* ============================================
   Trip details form — collects inputs and
   requests a range prediction from the backend
   ============================================ */

/* Client-side fallback formula, used only if the Python backend
   (app.py) is unreachable. Keeps the demo usable standalone.
   Base range figures are indicative averages per full charge. */
function estimateRangeFallback(vehicleType, inputs) {
  const baseRangeByType = {
    "2-wheeler": 85,
    "3-wheeler": 110,
    "4-wheeler": 320,
    "lorry": 180,
  };

  let range = baseRangeByType[vehicleType] * (inputs.currentCharge / 100);
  const factors = [];

  // Weather impact — EV batteries lose efficiency in heat and cold extremes
  if (inputs.weather > 38) {
    range *= 0.88;
    factors.push({ label: "High outside temperature", impact: "-12%", type: "neg" });
  } else if (inputs.weather < 15) {
    range *= 0.82;
    factors.push({ label: "Cold weather", impact: "-18%", type: "neg" });
  } else {
    factors.push({ label: "Comfortable weather", impact: "0%", type: "pos" });
  }

  // AC impact (4-wheeler / lorry)
  if (inputs.ac === "on") {
    range *= 0.85;
    factors.push({ label: "Air conditioning on", impact: "-15%", type: "neg" });
  }

  // Riders (2/3 wheeler)
  if (inputs.riders && inputs.riders > 1) {
    range *= 1 - 0.06 * (inputs.riders - 1);
    factors.push({ label: `${inputs.riders} riders on board`, impact: `-${6 * (inputs.riders - 1)}%`, type: "neg" });
  }

  // Load (3-wheeler / lorry)
  if (inputs.load && inputs.load > 0) {
    const loadPenalty = Math.min(0.3, inputs.load / 2000);
    range *= 1 - loadPenalty;
    factors.push({ label: `Carrying ${inputs.load} kg load`, impact: `-${Math.round(loadPenalty * 100)}%`, type: "neg" });
  }

  // Full load flag (lorry)
  if (inputs.fullload === "yes") {
    range *= 0.8;
    factors.push({ label: "Fully loaded vehicle", impact: "-20%", type: "neg" });
  }

  // Terrain
  if (inputs.terrain === "hilly") {
    range *= 0.78;
    factors.push({ label: "Hilly / ghat terrain", impact: "-22%", type: "neg" });
  } else {
    factors.push({ label: "Flat, steady terrain", impact: "0%", type: "pos" });
  }

  // Road & speed type — sustained highway speed drains charge fastest due to
  // aerodynamic drag; stop-and-go traffic drains less per km but loses some
  // efficiency to frequent acceleration (partly offset by regen braking).
  if (inputs.roadType === "highway") {
    range *= 0.82;
    factors.push({ label: "Sustained highway speed", impact: "-18%", type: "neg" });
  } else if (inputs.roadType === "traffic") {
    range *= 0.9;
    factors.push({ label: "Stop-and-go traffic road", impact: "-10%", type: "neg" });
  } else if (inputs.roadType === "mixed") {
    range *= 0.92;
    factors.push({ label: "Mixed highway + city roads", impact: "-8%", type: "neg" });
  }

  return { range: Math.round(range), factors };
}

document.getElementById("details-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const vehicleType = localStorage.getItem("ev_vehicle_type") || "4-wheeler";

  const inputs = {
    currentCharge: Number(document.getElementById("current-charge").value),
    weather: Number(document.getElementById("weather").value),
    ac: document.querySelector('input[name="ac"]:checked')?.value || "off",
    riders: Number(document.getElementById("riders").value) || 1,
    load: Number(document.getElementById("load").value) || 0,
    fullload: document.querySelector('input[name="fullload"]:checked')?.value || "no",
    terrain: document.getElementById("terrain").value,
    roadType: document.getElementById("road-type").value,
  };

  const start = document.getElementById("start").value.trim();
  const destination = document.getElementById("destination").value.trim();

  let result;
  try {
    const res = await fetch(API_BASE + "/predict-range", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: localStorage.getItem("ev_user_id"),
        vehicle_type: vehicleType,
        ...inputs,
        start,
        destination,
      }),
    });
    if (!res.ok) throw new Error("Prediction request failed");
    result = await res.json(); // { range, factors }
  } catch (err) {
    console.warn("Backend unreachable, using client-side fallback estimate.", err);
    result = estimateRangeFallback(vehicleType, inputs);
  }

  localStorage.setItem("ev_last_result", JSON.stringify(result));
  localStorage.setItem("ev_start_place", start);
  localStorage.setItem("ev_destination_place", destination);

  window.location.href = "result.html";
});
