# EV RangeFinder — Full-Stack (Python + SQLite), Deploy-Only Guide

This is a **real Python backend with a real database** — but built so that
you never have to connect anything yourself. One Flask app does everything:

```
Your browser  --->  app.py (Flask)  --->  ev_rangefinder.db (SQLite)
                        |
                        +--> also calls OpenStreetMap (Nominatim + Overpass)
                             for real nearby EV charging stations
```

- `app.py` serves the website pages (from `/public`) **and** the `/api/...`
  endpoints, in the same process. There is no separate frontend server and
  no separate backend server — so there's nothing for you to "connect."
- The database is **SQLite**: a single file (`ev_rangefinder.db`) that Flask
  creates automatically the first time it runs. No database server to
  install, no password to configure.

Your only job: get these files onto a hosting platform and click deploy.
Below is the simplest path — everything is drag-and-drop or button clicks.

---

## Step 1 — Put the files on GitHub (drag and drop, no commands)

1. Go to github.com and create a free account if you don't have one.
2. Click the **+** icon (top right) → **New repository**. Name it
   `ev-rangefinder` → **Create repository**.
3. On the new repo page, click **"uploading an existing file"**.
4. Drag the *entire* `ev-fullstack` folder (all files and subfolders:
   `app.py`, `requirements.txt`, `Procfile`, `public/`, etc.) into the
   upload box. GitHub keeps the folder structure automatically.
5. Scroll down, click **Commit changes**.

That's it — no git, no terminal, just drag-and-drop in the browser.

---

## Step 2 — Deploy it on Render (a few clicks)

1. Go to **render.com** → sign up (you can sign up with your GitHub account
   directly, which makes the next step one click).
2. Click **New +** → **Web Service**.
3. Choose **"Build and deploy from a Git repository"** and select the
   `ev-rangefinder` repo you just created.
4. Render will show a settings form. Fill in exactly:
   - **Name**: `ev-rangefinder` (or anything you like)
   - **Region**: closest to you
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
5. Click **Create Web Service**.

Render will now install everything and start your app automatically. Watch
the log panel — when it says something like `Your service is live`, click
the URL at the top of the page (looks like
`https://ev-rangefinder.onrender.com`). That link is your live website —
share it with anyone.

---

## What to expect

- First load after inactivity can take ~30–50 seconds on Render's free
  tier (it "sleeps" the app when nobody's using it, then wakes back up).
  This is a free-tier limitation, not a bug in the project.
- The SQLite database file resets if the app is redeployed or the free
  instance is recreated. For a college project demo this is completely
  fine — it isn't meant to be a permanent production database.
- Everything else (login, vehicle selection, mileage prediction, nearest
  charging stations, feedback) works exactly the same as it did locally.

## If you ever want to preview it on your own computer first

You don't have to — but if you're curious, the whole thing is still just:
```
pip install -r requirements.txt
python app.py
```
then opening `http://localhost:5000` in a browser. Not required for
deployment — Render does this same thing automatically on its own servers.
