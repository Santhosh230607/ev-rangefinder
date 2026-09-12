/* ============================================
   Login / Signup page logic
   ============================================ */

const API_BASE = "/api"; // same server serves the site and the API — nothing to connect

let mode = "login"; // or "signup"

const nameField = document.getElementById("name-field");
const toggleModeLink = document.getElementById("toggle-mode");
const toggleText = document.getElementById("toggle-text");
const formTitle = document.getElementById("form-title");
const submitBtn = document.getElementById("submit-btn");
const authError = document.getElementById("auth-error");

toggleModeLink.addEventListener("click", (e) => {
  e.preventDefault();
  mode = mode === "login" ? "signup" : "login";

  if (mode === "signup") {
    nameField.classList.remove("hidden");
    formTitle.textContent = "Create your account";
    submitBtn.textContent = "Create account";
    toggleText.textContent = "Already have an account?";
    toggleModeLink.textContent = "Sign in";
  } else {
    nameField.classList.add("hidden");
    formTitle.textContent = "Sign in to your account";
    submitBtn.textContent = "Sign in";
    toggleText.textContent = "New here?";
    toggleModeLink.textContent = "Create an account";
  }
});

document.getElementById("auth-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  authError.style.display = "none";

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const name = document.getElementById("name").value.trim();

  const endpoint = mode === "signup" ? "/register" : "/login";
  const payload = mode === "signup" ? { name, email, password } : { email, password };

  try {
    const res = await fetch(API_BASE + endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      authError.textContent = data.message || "Check your email and password and try again.";
      authError.style.display = "block";
      return;
    }

    // Store a simple session token/user id locally
    localStorage.setItem("ev_user_id", data.user_id);
    localStorage.setItem("ev_user_name", data.name || name);
    window.location.href = "select-vehicle.html";
  } catch (err) {
    // Backend not reachable — fall back to a local-only demo session
    console.warn("Backend unreachable, continuing in offline demo mode.", err);
    localStorage.setItem("ev_user_id", "demo");
    localStorage.setItem("ev_user_name", name || email.split("@")[0]);
    window.location.href = "select-vehicle.html";
  }
});
