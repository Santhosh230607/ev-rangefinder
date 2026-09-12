/* ============================================
   EV RangeFinder — shared front-end behaviour
   ============================================ */

const API_BASE = "/api"; // same server serves the site and the API — nothing to connect

/* ---- Toggle group buttons (AC on/off, full load yes/no) ---- */
document.querySelectorAll(".toggle-group").forEach((group) => {
  group.querySelectorAll(".toggle-option").forEach((option) => {
    option.addEventListener("click", () => {
      group.querySelectorAll(".toggle-option").forEach((o) => o.classList.remove("active"));
      option.classList.add("active");
      option.querySelector("input").checked = true;
    });
  });
});

/* ---- Show only the fields relevant to the selected vehicle type ---- */
(function setupVehicleSpecificFields() {
  const detailsForm = document.getElementById("details-form");
  if (!detailsForm) return; // not on details.html

  const vehicleType = localStorage.getItem("ev_vehicle_type") || "4-wheeler";

  const titleMap = {
    "2-wheeler": "Tell us about your ride",
    "3-wheeler": "Tell us about your trip",
    "4-wheeler": "Tell us about this drive",
    "lorry": "Tell us about this haul",
  };
  document.getElementById("page-title").textContent = titleMap[vehicleType];

  const fieldVisibility = {
    "2-wheeler": ["riders-field"],
    "3-wheeler": ["riders-field", "load-field"],
    "4-wheeler": ["ac-field"],
    "lorry": ["ac-field", "load-field", "fullload-field"],
  };

  (fieldVisibility[vehicleType] || []).forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("hidden");
  });
})();
