"""
EV RangeFinder — one-process full-stack app
=============================================
This single file:
  1. Serves the website itself (everything in /public)
  2. Provides the /api/... endpoints the JS calls
  3. Creates and talks to its own SQLite database automatically

Because the frontend and backend are served by the SAME app, there is
nothing to "connect" — the browser just talks to whatever address this
app is running on, whether that's your computer or a hosting platform.

Local run (optional, only if you want to preview it yourself):
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000 in a browser.

For deployment, see README.md — it's a drag-and-drop + click-deploy flow.
"""

import os
import sqlite3
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

from flask import Flask, request, jsonify, redirect, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)

FRONTEND_FILES = {
    "login.html", "select-vehicle.html", "details.html", "result.html",
    "feedback.html", "style.css", "script.js", "auth.js", "mileage.js",
    "result.js", "feedback.js",
}

# ------------------------------------------------------------------
# Database (SQLite — a single file, created automatically, no server,
# no password, no separate install. Lives next to this script.)
# ------------------------------------------------------------------
DB_PATH = os.path.join(BASE_DIR, "ev_rangefinder.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            vehicle_type TEXT NOT NULL,
            current_charge_pct REAL,
            weather_c REAL,
            ac_on INTEGER DEFAULT 0,
            riders INTEGER DEFAULT 1,
            load_kg REAL DEFAULT 0,
            full_load INTEGER DEFAULT 0,
            terrain TEXT DEFAULT 'flat',
            road_type TEXT DEFAULT 'mixed',
            start_place TEXT,
            destination_place TEXT,
            predicted_range_km REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            rating INTEGER,
            actual_range_km REAL,
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    conn.commit()
    conn.close()


init_db()  # runs the moment the app starts — no manual schema step, ever


# ------------------------------------------------------------------
# Mileage / range prediction model
# ------------------------------------------------------------------
BASE_RANGE_KM = {"2-wheeler": 85, "3-wheeler": 110, "4-wheeler": 320, "lorry": 180}


def predict_range(vehicle_type: str, data: dict) -> dict:
    base = BASE_RANGE_KM.get(vehicle_type, 150)
    charge_pct = float(data.get("currentCharge", 100))
    range_km = base * (charge_pct / 100)
    factors = []

    weather = float(data.get("weather", 25))
    if weather > 38:
        range_km *= 0.88
        factors.append({"label": "High outside temperature", "impact": "-12%", "type": "neg"})
    elif weather < 15:
        range_km *= 0.82
        factors.append({"label": "Cold weather", "impact": "-18%", "type": "neg"})
    else:
        factors.append({"label": "Comfortable weather", "impact": "0%", "type": "pos"})

    if data.get("ac") == "on":
        range_km *= 0.85
        factors.append({"label": "Air conditioning on", "impact": "-15%", "type": "neg"})

    riders = int(data.get("riders", 1) or 1)
    if riders > 1:
        penalty = 0.06 * (riders - 1)
        range_km *= (1 - penalty)
        factors.append({"label": f"{riders} riders on board", "impact": f"-{round(penalty * 100)}%", "type": "neg"})

    load_kg = float(data.get("load", 0) or 0)
    if load_kg > 0:
        load_penalty = min(0.30, load_kg / 2000)
        range_km *= (1 - load_penalty)
        factors.append({"label": f"Carrying {int(load_kg)} kg load", "impact": f"-{round(load_penalty * 100)}%", "type": "neg"})

    if data.get("fullload") == "yes":
        range_km *= 0.80
        factors.append({"label": "Fully loaded vehicle", "impact": "-20%", "type": "neg"})

    terrain = data.get("terrain", "flat")
    if terrain == "hilly":
        range_km *= 0.78
        factors.append({"label": "Hilly / ghat terrain", "impact": "-22%", "type": "neg"})
    else:
        factors.append({"label": "Flat, steady terrain", "impact": "0%", "type": "pos"})

    road_type = data.get("roadType", "mixed")
    if road_type == "highway":
        range_km *= 0.82
        factors.append({"label": "Sustained highway speed", "impact": "-18%", "type": "neg"})
    elif road_type == "traffic":
        range_km *= 0.90
        factors.append({"label": "Stop-and-go traffic road", "impact": "-10%", "type": "neg"})
    elif road_type == "mixed":
        range_km *= 0.92
        factors.append({"label": "Mixed highway + city roads", "impact": "-8%", "type": "neg"})

    return {"range": round(range_km), "factors": factors}


# ------------------------------------------------------------------
# Geocoding + nearby EV stations (OpenStreetMap — free, no API key)
# ------------------------------------------------------------------
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "EV-RangeFinder-Student-Project/1.0"


def geocode_place(place_name: str):
    params = {"q": place_name, "format": "json", "limit": 1}
    resp = requests.get(NOMINATIM_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=10)
    resp.raise_for_status()
    results = resp.json()
    if not results:
        return None
    return float(results[0]["lat"]), float(results[0]["lon"])


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


def find_nearby_stations(lat, lon, radius_m=8000, limit=6):
    query = f"""
    [out:json][timeout:15];
    node["amenity"="charging_station"](around:{radius_m},{lat},{lon});
    out body {limit * 3};
    """
    resp = requests.post(OVERPASS_URL, data={"data": query}, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    elements = resp.json().get("elements", [])

    stations = []
    for el in elements:
        tags = el.get("tags", {})
        s_lat, s_lon = el.get("lat"), el.get("lon")
        if s_lat is None or s_lon is None:
            continue
        stations.append({
            "name": tags.get("name", "EV Charging Station"),
            "address": tags.get("addr:street", tags.get("operator", "")),
            "distance_km": haversine_km(lat, lon, s_lat, s_lon),
        })

    stations.sort(key=lambda s: s["distance_km"])
    return stations[:limit]


# ------------------------------------------------------------------
# Routes — serving the site
# ------------------------------------------------------------------
@app.route("/")
def home():
    return redirect("/login.html")


@app.route("/<path:filename>")
def frontend_file(filename):
    if filename not in FRONTEND_FILES:
        return jsonify({"message": "Not found"}), 404
    return send_from_directory(BASE_DIR, filename)


# ------------------------------------------------------------------
# Routes — the API the frontend JS calls
# ------------------------------------------------------------------
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not (name and email and password):
        return jsonify({"message": "Name, email and password are all required."}), 400

    conn = get_db()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return jsonify({"message": "An account with this email already exists."}), 409

        password_hash = generate_password_hash(password)
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        return jsonify({"user_id": cur.lastrowid, "name": name}), 201
    finally:
        conn.close()


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email, password = data.get("email"), data.get("password")

    conn = get_db()
    try:
        user = conn.execute(
            "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"message": "Check your email and password and try again."}), 401
        return jsonify({"user_id": user["id"], "name": user["name"]}), 200
    finally:
        conn.close()


@app.route("/api/predict-range", methods=["POST"])
def predict_range_endpoint():
    data = request.get_json(force=True)
    vehicle_type = data.get("vehicle_type", "4-wheeler")
    result = predict_range(vehicle_type, data)

    conn = get_db()
    try:
        user_id = data.get("user_id")
        user_id = int(user_id) if str(user_id).isdigit() else None
        conn.execute(
            """
            INSERT INTO trips (
                user_id, vehicle_type, current_charge_pct, weather_c, ac_on,
                riders, load_kg, full_load, terrain, road_type, start_place,
                destination_place, predicted_range_km, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                user_id,
                vehicle_type,
                data.get("currentCharge"),
                data.get("weather"),
                1 if data.get("ac") == "on" else 0,
                data.get("riders", 1),
                data.get("load", 0),
                1 if data.get("fullload") == "yes" else 0,
                data.get("terrain", "flat"),
                data.get("roadType", "mixed"),
                data.get("start"),
                data.get("destination"),
                result["range"],
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    except sqlite3.Error as err:
        app.logger.warning(f"Could not log trip: {err}")
    finally:
        conn.close()

    return jsonify(result), 200


@app.route("/api/nearest-stations", methods=["GET"])
def nearest_stations_endpoint():
    place = request.args.get("place", "").strip()
    if not place:
        return jsonify({"message": "A 'place' query parameter is required."}), 400
    try:
        coords = geocode_place(place)
        if coords is None:
            return jsonify([]), 200
        lat, lon = coords
        stations = find_nearby_stations(lat, lon)
        return jsonify(stations), 200
    except requests.RequestException as err:
        app.logger.error(f"Station lookup failed: {err}")
        return jsonify({"message": "Could not reach the map service right now."}), 502


@app.route("/api/feedback", methods=["POST"])
def feedback_endpoint():
    data = request.get_json(force=True)
    conn = get_db()
    try:
        user_id = data.get("user_id")
        user_id = int(user_id) if str(user_id).isdigit() else None
        conn.execute(
            "INSERT INTO feedback (user_id, rating, actual_range_km, comment, created_at) VALUES (?,?,?,?,?)",
            (
                user_id,
                data.get("rating"),
                data.get("actual_range"),
                data.get("comment", ""),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return jsonify({"message": "Thanks — your feedback was recorded."}), 201
    finally:
        conn.close()


if __name__ == "__main__":
    # Hosting platforms set PORT automatically; 5000 is used for local preview.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
