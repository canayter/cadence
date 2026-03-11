# ScrobbleForge

> **"Your listening history, forged into words."**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Last.fm](https://img.shields.io/badge/Last.fm-API-D51007?style=flat-square&logo=last.fm&logoColor=white)
![Bluesky](https://img.shields.io/badge/Bluesky-AT_Protocol-0085FF?style=flat-square&logo=bluesky&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)

ScrobbleForge pulls your Last.fm scrobble history, distills it into beautifully formatted listening digest summaries, and publishes them as threaded posts directly to Bluesky — all from a clean, dark-themed web UI.

---

## Overview

If you scrobble, you have data. Lots of it. ScrobbleForge turns that data into something worth sharing: curated weekly recaps, monthly deep-dives, or year-in-review threads that land on Bluesky as native, properly threaded posts. No copy-pasting. No formatting by hand. Just forge and post.

```
 ┌─────────────┐        ┌──────────────────┐        ┌─────────────┐
 │   Last.fm   │ ──────▶│  ScrobbleForge   │──────▶ │  Bluesky   │
 │  Scrobbles  │  fetch │  Filter · Format │  post  │  Thread    │
 └─────────────┘        │  Digest · Style  │        └─────────────┘
                        └──────────────────┘
                          Streamlit Web UI
```

---

## Features

- **Time range selector** — Week, month, 3 months, 6 months, year, or all-time overall
- **Top artists, tracks & albums** — Play counts pulled directly from the Last.fm API
- **Digest filtering** — Choose exactly what makes it into the post: artists, tracks, albums, listening stats
- **Multiple digest styles** — `DEFAULT_STYLE` and extensible formatting options
- **Bluesky thread builder** — Constructs properly structured AT Protocol thread posts from your data
- **One-click publishing** — Post to your Bluesky account directly from the UI
- **Dark-themed Streamlit UI** — Void background, cyan accent, Space Grotesk + JetBrains Mono typography — consistent with the Forge design system
- **Metric cards & progress indicators** — See your stats at a glance before you post

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/canayter/scrobbleforge.git
cd scrobbleforge

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your environment
cp .env.example .env
# Open .env and fill in your API keys (see Configuration below)

# 4. Run the app
streamlit run app.py
```

The UI will open at `http://localhost:8501`.

---

## Configuration

ScrobbleForge reads credentials from a `.env` file in the project root. Never commit this file.

```dotenv
# .env

# Last.fm — get your key at https://www.last.fm/api/account/create
LASTFM_API_KEY=your_lastfm_api_key_here
LASTFM_USERNAME=your_lastfm_username_here

# Bluesky — use an App Password, not your main password
# Generate one at: Settings → Privacy & Security → App Passwords
BLUESKY_HANDLE=yourhandle.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

| Variable             | Where to get it                                              |
|----------------------|--------------------------------------------------------------|
| `LASTFM_API_KEY`     | [last.fm/api](https://www.last.fm/api/account/create)        |
| `LASTFM_USERNAME`    | Your Last.fm profile username                                |
| `BLUESKY_HANDLE`     | Your full Bluesky handle (e.g. `you.bsky.social`)            |
| `BLUESKY_APP_PASSWORD` | Settings → Privacy & Security → App Passwords in Bluesky  |

---

## Architecture

The project is intentionally modular. Each file has one job:

```
scrobbleforge/
├── app.py          # Streamlit UI — dark theme, layout, user controls
├── lastfm.py       # Last.fm API client — scrobble fetching, top artists/tracks/albums
├── digest.py       # Digest engine — apply_filters(), build_thread_posts(), DEFAULT_STYLE
├── bluesky.py      # Bluesky poster — AT Protocol thread construction via atproto
├── requirements.txt
└── .env            # Your secrets (gitignored)
```

### Data flow

1. **`lastfm.py`** fetches raw scrobble data and top lists for the selected time period via the Last.fm API.
2. **`digest.py`** applies your filter choices and formats the data into structured post content using the configured style.
3. **`bluesky.py`** takes the list of formatted post strings and publishes them as a native AT Protocol reply-thread on Bluesky.
4. **`app.py`** orchestrates all of the above through a Streamlit interface, handling state, previews, and the post action.

### Dependencies

| Package            | Role                                      | Min version |
|--------------------|-------------------------------------------|-------------|
| `streamlit`        | Web UI framework                          | `>=1.32.0`  |
| `pandas`           | Data processing and aggregation           | `>=2.0.0`   |
| `requests`         | HTTP client for the Last.fm API           | `>=2.31.0`  |
| `python-dotenv`    | `.env` file loading                       | `>=1.0.0`   |
| `atproto`          | Bluesky / AT Protocol SDK                 | `>=0.0.54`  |

---

## Use Cases

- **Weekly recap thread** — Schedule a Monday morning post recapping last week's listening
- **Monthly listening review** — Month-end digest with your top artists and standout tracks
- **Year-in-review thread** — A narrative alternative to Spotify Wrapped, on your terms
- **Music discovery sharing** — Let your followers see what you have been into lately
- **Personal analytics dashboard** — Use the UI purely to explore your own stats without posting

---

## Roadmap

- [ ] Scheduling — post digests automatically on a cron/timer
- [ ] Custom style templates — user-defined post formatting in the UI
- [ ] Artist image embeds — attach album art to posts (Bluesky blob support)
- [ ] Listening streaks and milestones — highlight personal records in the digest
- [ ] Multi-account support — manage multiple Last.fm/Bluesky pairs
- [ ] Export to Markdown / plain text — for archiving or cross-posting elsewhere

---

## Author

Built by **[Can Ayter](https://ayter.com)** — part of the Forge suite of tools.

> *ScrobbleForge is an independent project and is not affiliated with Last.fm or Bluesky.*
