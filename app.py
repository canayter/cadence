import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
from lastfm import LastFMClient
from digest import apply_filters, build_thread_posts
from bluesky import BlueskyPoster

load_dotenv()

st.set_page_config(
    page_title="ScrobbleForge",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── GlossaForge-inspired theme ────────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
  :root {
    --void:     #06060e;
    --base:     #0d0d18;
    --raised:   #12121f;
    --surface:  #181828;
    --lift:     #1e1e30;
    --hover:    #252538;
    --border:   rgba(255,255,255,0.07);
    --border2:  rgba(255,255,255,0.14);
    --cyan:     #00d4ff;
    --cyan-dim: rgba(0,212,255,0.10);
    --cyan-glow:rgba(0,212,255,0.28);
    --violet:   #8b5cf6;
    --ink:      #eeeef5;
    --ink-mid:  #9898b0;
    --ink-low:  #5a5a72;
    --r:        8px;
    --r-lg:     14px;
    --r-full:   9999px;
    --ease:     cubic-bezier(0.16,1,0.3,1);
  }

  html, body, [class*="css"] {
    font-family: 'Space Grotesk', system-ui, sans-serif !important;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background: var(--raised) !important;
    border-right: 1px solid var(--border2);
  }
  section[data-testid="stSidebar"] .stMarkdown hr {
    border-color: var(--border2);
  }

  /* Main background */
  .stApp { background: var(--base) !important; }
  .block-container { padding-top: 2rem !important; }

  /* Metric / KPI cards */
  .metric-card {
    background: linear-gradient(135deg, #006080 0%, #003d52 100%);
    border: 1px solid var(--cyan-glow);
    padding: 20px 24px;
    border-radius: var(--r-lg);
    color: var(--ink);
    margin-bottom: 10px;
  }
  .metric-card-violet {
    background: linear-gradient(135deg, #3b1f6b 0%, #251345 100%);
    border: 1px solid rgba(139,92,246,0.35);
    padding: 20px 24px;
    border-radius: var(--r-lg);
    color: var(--ink);
    margin-bottom: 10px;
  }
  .metric-card-cyan {
    background: linear-gradient(135deg, #004f66 0%, #002d3d 100%);
    border: 1px solid var(--cyan-glow);
    padding: 20px 24px;
    border-radius: var(--r-lg);
    color: var(--ink);
    margin-bottom: 10px;
  }
  .metric-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-mid);
    margin: 0 0 4px 0;
  }
  .metric-value {
    font-size: 1.75rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink);
    margin: 0;
  }
  .metric-accent { color: var(--cyan); }

  /* Post preview boxes */
  .post-preview {
    background: var(--raised);
    border: 1px solid var(--border2);
    border-left: 4px solid var(--cyan);
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem;
    line-height: 1.6;
    padding: 14px 16px;
    border-radius: var(--r);
    color: var(--ink);
    white-space: pre-wrap;
    margin: 6px 0 2px 0;
  }
  .post-number {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--cyan);
    margin-bottom: 4px;
  }
  .char-count { font-size: 0.72rem; color: var(--ink-low); margin: 2px 0 16px 0; }
  .char-over  { font-size: 0.72rem; color: #f87171; font-weight: 700; margin: 2px 0 16px 0; }

  /* Warning banner when filters yield no results */
  .empty-state {
    background: var(--raised);
    border: 1px solid var(--border2);
    border-left: 4px solid var(--violet);
    padding: 16px 20px;
    border-radius: var(--r);
    color: var(--ink-mid);
    margin: 16px 0;
  }

  /* Headings */
  h1 { font-weight: 700 !important; letter-spacing: -0.03em !important; }
  h2, h3 { font-weight: 600 !important; letter-spacing: -0.02em !important; }

  /* Sidebar section labels */
  .sidebar-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ink-mid);
    margin-bottom: 8px;
  }

  /* Success/error feedback */
  .post-success {
    background: rgba(52,211,153,0.08);
    border: 1px solid rgba(52,211,153,0.3);
    border-radius: var(--r);
    padding: 14px 16px;
    color: #34d399;
    font-size: 0.9rem;
  }
  .post-error {
    background: rgba(248,113,113,0.08);
    border: 1px solid rgba(248,113,113,0.3);
    border-radius: var(--r);
    padding: 14px 16px;
    color: #f87171;
    font-size: 0.9rem;
  }

  /* Divider */
  hr { border-color: var(--border2) !important; }

  /* Dataframe */
  .stDataFrame { border-radius: var(--r-lg) !important; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
for key, default in [
    ('digest_data',    None),
    ('posts_preview',  []),
    ('post_status',    None),
    ('post_uris',      []),
    ('lastfm_token',   None),   # pending auth token
    ('lastfm_sk',      os.getenv("LASTFM_SESSION_KEY", "")),  # session key
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:\'Space Grotesk\',sans-serif;font-size:1.15rem;font-weight:700;letter-spacing:-0.02em;padding:4px 0 16px 0;">Scrobble<span style="color:#00d4ff;">Forge</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-label">Last.fm</div>', unsafe_allow_html=True)

    username = st.text_input(
        "Username",
        value=os.getenv("LASTFM_USERNAME", ""),
        placeholder="your_lastfm_username",
        label_visibility="collapsed",
    )
    period = st.selectbox("Period", ["weekly", "monthly"])

    # ── Last.fm auth (required for private profiles) ──────────────────────
    st.divider()
    st.markdown('<div class="sidebar-label">Last.fm Auth</div>', unsafe_allow_html=True)

    if st.session_state.lastfm_sk:
        st.markdown(
            '<div style="color:#34d399;font-size:0.8rem;">✓ Connected</div>',
            unsafe_allow_html=True,
        )
        if st.button("Disconnect", use_container_width=True):
            st.session_state.lastfm_sk    = ""
            st.session_state.lastfm_token = None
            st.rerun()
        st.caption("Save this to .env to skip auth next time:")
        st.code(st.session_state.lastfm_sk, language=None)
    else:
        st.caption("Required for private profiles.")

        # Step 1 — get a token and show auth URL
        if st.button("Step 1 — Get auth link", use_container_width=True):
            try:
                from lastfm import LastFMClient as _LFM
                token, auth_url = _LFM(username or "x").get_auth_token()
                st.session_state.lastfm_token = token
                st.session_state._auth_url    = auth_url
            except Exception as e:
                st.error(f"Could not get token: {e}")

        if st.session_state.lastfm_token:
            auth_url = getattr(st.session_state, '_auth_url', '')
            st.markdown(
                f'<a href="{auth_url}" target="_blank" style="color:#00d4ff;font-size:0.82rem;">'
                '→ Authorize on Last.fm</a>',
                unsafe_allow_html=True,
            )
            st.caption("After authorizing in your browser, click below.")

            # Step 3 — exchange token for session key
            if st.button("Step 2 — Complete connection", use_container_width=True):
                try:
                    from lastfm import LastFMClient as _LFM
                    client = _LFM(username or "x")
                    sk = client.exchange_token_for_session(st.session_state.lastfm_token)
                    st.session_state.lastfm_sk    = sk
                    st.session_state.lastfm_token = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Auth failed — did you authorize the link first? ({e})")

    st.divider()
    st.markdown('<div class="sidebar-label">Filters (optional)</div>', unsafe_allow_html=True)
    filter_album = st.text_input("Album", placeholder="e.g. OK Computer")
    filter_genre = st.text_input("Genre / tag", placeholder="e.g. indie rock")
    filter_track = st.text_input("Track", placeholder="e.g. Karma Police")

    st.divider()
    st.markdown('<div class="sidebar-label">Bluesky</div>', unsafe_allow_html=True)
    bsky_handle = st.text_input(
        "Handle",
        value=os.getenv("BLUESKY_HANDLE", ""),
        placeholder="yourname.bsky.social",
    )
    bsky_password = st.text_input(
        "App Password",
        type="password",
        value=os.getenv("BLUESKY_APP_PASSWORD", ""),
        placeholder="xxxx-xxxx-xxxx-xxxx",
    )
    st.caption("Create an app password in Bluesky Settings → Privacy & Security → App Passwords.")

    st.divider()
    fetch_btn = st.button("Fetch Digest", type="primary", use_container_width=True)

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(
    '<h1 style="margin-bottom:4px;">Scrobble<span style="color:#00d4ff;">Forge</span></h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p style="color:#9898b0;margin-top:0;font-size:0.95rem;">Last.fm → Bluesky digest generator</p>',
    unsafe_allow_html=True,
)

# ── Fetch ─────────────────────────────────────────────────────────────────────
if fetch_btn:
    if not username:
        st.error("Please enter a Last.fm username in the sidebar.")
    else:
        with st.spinner("Fetching scrobble data from Last.fm…"):
            try:
                client   = LastFMClient(
                    username=username,
                    session_key=st.session_state.lastfm_sk or None,
                )
                raw_data = client.get_digest_data(period)
                filtered = apply_filters(
                    raw_data,
                    filter_album=filter_album or None,
                    filter_genre=filter_genre or None,
                    filter_track=filter_track or None,
                )
                st.session_state.digest_data   = filtered
                st.session_state.posts_preview = build_thread_posts(filtered)
                st.session_state.post_status   = None
                st.session_state.post_uris     = []
            except Exception as e:
                st.error(f"Error fetching data: {e}")

# ── Main content (only shown after a fetch) ───────────────────────────────────
if st.session_state.digest_data:
    data = st.session_state.digest_data

    # Empty state after filters
    if data['total_scrobbles'] == 0:
        st.markdown(
            '<div class="empty-state">No scrobbles match the current filters. Try relaxing your filter criteria.</div>',
            unsafe_allow_html=True,
        )
    else:
        # ── KPI row ───────────────────────────────────────────────────────────
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-label">Total Scrobbles</p>
                <p class="metric-value metric-accent">{data['total_scrobbles']}</p>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card-violet">
                <p class="metric-label">Listening Hours</p>
                <p class="metric-value">~{data['listening_hours']} hrs</p>
            </div>""", unsafe_allow_html=True)

        with col3:
            top_artist_name = ''
            if data['top_artists']:
                a = data['top_artists'][0]
                top_artist_name = a.get('name') or a.get('artist', '')
            st.markdown(f"""
            <div class="metric-card-cyan">
                <p class="metric-label">Top Artist</p>
                <p class="metric-value" style="font-size:1.3rem;">{top_artist_name or '—'}</p>
            </div>""", unsafe_allow_html=True)

        st.divider()

        # ── Thread preview ────────────────────────────────────────────────────
        st.markdown("### Thread Preview")
        st.markdown('<p style="color:#9898b0;font-size:0.85rem;margin-top:-8px;">Each block is one Bluesky post · 300 char limit</p>', unsafe_allow_html=True)

        for i, post in enumerate(st.session_state.posts_preview, 1):
            char_count = len(post)
            is_over    = char_count > 300
            st.markdown(f'<div class="post-number">Post {i} / {len(st.session_state.posts_preview)}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="post-preview">{post}</div>', unsafe_allow_html=True)
            count_class = "char-over" if is_over else "char-count"
            st.markdown(f'<div class="{count_class}">{char_count} / 300</div>', unsafe_allow_html=True)

        st.divider()

        # ── Top charts tabs ───────────────────────────────────────────────────
        st.markdown("### Charts")
        tab1, tab2, tab3 = st.tabs(["Top Artists", "Top Tracks", "Top Albums"])

        with tab1:
            if data['top_artists']:
                artists_df = pd.DataFrame(data['top_artists'])
                artists_df.index = artists_df.index + 1
                st.dataframe(artists_df, use_container_width=True)
            else:
                st.caption("No artist data.")

        with tab2:
            if data['top_tracks']:
                tracks_df = pd.DataFrame(data['top_tracks'])
                tracks_df.index = tracks_df.index + 1
                st.dataframe(tracks_df, use_container_width=True)
            else:
                st.caption("No track data.")

        with tab3:
            if data['top_albums']:
                albums_df = pd.DataFrame(data['top_albums'])
                albums_df.index = albums_df.index + 1
                st.dataframe(albums_df, use_container_width=True)
            else:
                st.caption("No album data.")

        st.divider()

        # ── Post to Bluesky ───────────────────────────────────────────────────
        st.markdown("### Post to Bluesky")

        creds_ready = bool(bsky_handle and bsky_password)
        if not creds_ready:
            st.markdown(
                '<p style="color:#9898b0;font-size:0.85rem;">Enter your Bluesky handle and app password in the sidebar to enable posting.</p>',
                unsafe_allow_html=True,
            )

        post_btn = st.button(
            "Post Thread to Bluesky",
            type="primary",
            disabled=not creds_ready,
        )

        if post_btn and creds_ready:
            poster = BlueskyPoster(handle=bsky_handle, app_password=bsky_password)
            errors = poster.validate_posts(st.session_state.posts_preview)
            if errors:
                for err in errors:
                    st.error(err)
            else:
                with st.spinner("Posting thread to Bluesky…"):
                    try:
                        uris = poster.post_thread(st.session_state.posts_preview)
                        st.session_state.post_status = 'success'
                        st.session_state.post_uris   = uris
                    except Exception as e:
                        st.session_state.post_status = 'error'
                        st.session_state.post_uris   = [str(e)]

        if st.session_state.post_status == 'success':
            st.markdown(
                f'<div class="post-success">Thread posted — {len(st.session_state.post_uris)} posts published.</div>',
                unsafe_allow_html=True,
            )
            for uri in st.session_state.post_uris:
                st.code(uri, language=None)

        elif st.session_state.post_status == 'error':
            st.markdown(
                f'<div class="post-error">Posting failed: {st.session_state.post_uris[0]}</div>',
                unsafe_allow_html=True,
            )

else:
    # Landing state — no data fetched yet
    st.markdown("""
    <div style="
        background: #12121f;
        border: 1px solid rgba(255,255,255,0.14);
        border-left: 4px solid #00d4ff;
        border-radius: 14px;
        padding: 32px 36px;
        margin-top: 24px;
        color: #9898b0;
        font-size: 0.92rem;
        line-height: 1.7;
    ">
        <p style="color:#eeeef5;font-size:1.05rem;font-weight:600;margin:0 0 12px 0;">Get started</p>
        <ol style="margin:0;padding-left:20px;">
            <li>Enter your <span style="color:#00d4ff;">Last.fm username</span> in the sidebar</li>
            <li>Choose a period (weekly or monthly)</li>
            <li>Optionally filter by album, genre, or track</li>
            <li>Click <strong style="color:#eeeef5;">Fetch Digest</strong> to generate your thread</li>
            <li>Add Bluesky credentials and post when ready</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
