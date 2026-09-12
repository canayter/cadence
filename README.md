# Cadence

*[Türkçe](README.tr.md)*

Turns Last.fm scrobble history into a proper Bluesky thread: top artists, tracks, and albums for a week, a month, or any range you pick, formatted and posted as a native AT Protocol thread instead of a screenshot or a copy-pasted list.

Formerly called ScrobbleForge. Same tool, shorter name.

**Try it in the browser:** [ayter.com/cadence](https://ayter.com/cadence) — a one-off version that runs entirely client-side, no install.
**Self-hosted app:** this repository, for the version that can post automatically every week.
**Author:** [Can Ayter](https://ayter.com)

## What it does

Pulls scrobbles for a chosen time range (week, month, 3 months, 6 months, year, or all-time) from the Last.fm API, lets you filter by artist, album, track, or genre before anything gets posted, and builds a properly threaded set of Bluesky posts from the result. A Streamlit UI wraps the whole thing — pick a range, preview the thread, post it.

**Auto-scheduling.** Start the scheduler from the UI with a day of the week and an hour, and the app posts your digest automatically every week from then on, as long as it keeps running. This isn't a separate cron job or hosted service — it's a background loop inside the running Streamlit app, which is why self-hosting it (rather than only using the one-off browser version) is what the scheduling feature needs.

## How it's organized

Each file has one job, which is what makes the auto-scheduler safe to add without touching the parts that already worked:

```
cadence/
├── app.py          Streamlit UI: layout, controls, the auto-scheduler loop
├── lastfm.py       Last.fm API client — scrobble fetching, top artists/tracks/albums
├── digest.py       filtering and formatting: apply_filters(), build_thread_posts()
├── bluesky.py      posts the formatted thread via the atproto SDK
└── requirements.txt
```

## Running it yourself

```bash
git clone https://github.com/canayter/cadence.git
cd cadence
pip install -r requirements.txt
cp .env.example .env    # fill in your Last.fm and Bluesky credentials
streamlit run app.py
```

`.env` needs a Last.fm API key and username, plus a Bluesky handle and an **app password** (generate one under Settings → Privacy & Security → App Passwords — never use your actual account password here).

## Dependencies

`streamlit`, `pandas`, `requests`, `python-dotenv`, and `atproto` for the Bluesky/AT Protocol side.

## Author

**Can Ayter** — [ayter.com](https://ayter.com)

Independent project, not affiliated with Last.fm or Bluesky. MIT License.
