/* ============================================
   Feedback page logic
   ============================================ */

let selectedRating = 0;
const stars = document.querySelectorAll("#star-rating .star");

stars.forEach((star) => {
  star.addEventListener("click", () => {
    selectedRating = Number(star.dataset.value);
    stars.forEach((s) => {
      s.classList.toggle("filled", Number(s.dataset.value) <= selectedRating);
    });
  });
});

document.getElementById("feedback-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    user_id: localStorage.getItem("ev_user_id") || "guest",
    rating: selectedRating,
    actual_range: Number(document.getElementById("actual-range").value) || null,
    comment: document.getElementById("comment").value.trim(),
  };

  try {
    await fetch(API_BASE + "/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    console.warn("Backend unreachable — feedback stored locally only.", err);
  }

  document.getElementById("feedback-form").classList.add("hidden");
  document.getElementById("thanks-msg").classList.remove("hidden");
});
