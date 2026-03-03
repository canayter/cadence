import pandas as pd
from datetime import datetime, timedelta

BLUESKY_LIMIT = 300


# ------------------------------------------------------------------
# Filtering
# ------------------------------------------------------------------

def apply_filters(
    data: dict,
    filter_album: str = None,
    filter_genre: str = None,
    filter_track: str = None,
) -> dict:
    """
    Applies optional filters to the digest data bundle.
    Filters work on the raw scrobble DataFrame and re-derive top lists
    so all stats reflect only the filtered scrobbles.
    """
    df: pd.DataFrame = data['df'].copy()

    if filter_album:
        df = df[df['album'].str.contains(filter_album, case=False, na=False)]

    if filter_genre:
        genre_lower = filter_genre.lower()
        df = df[df['tags'].apply(
            lambda tags: isinstance(tags, list) and genre_lower in tags
        )]

    if filter_track:
        df = df[df['track'].str.contains(filter_track, case=False, na=False)]

    if df.empty:
        return {
            **data,
            'df':              df,
            'top_artists':     [],
            'top_tracks':      [],
            'top_albums':      [],
            'total_scrobbles': 0,
            'listening_hours': 0.0,
        }

    filtered_top_artists = (
        df.groupby('artist').size()
          .sort_values(ascending=False)
          .head(10)
          .reset_index()
          .rename(columns={0: 'playcount'})
          .to_dict('records')
    )
    filtered_top_tracks = (
        df.groupby(['track', 'artist']).size()
          .sort_values(ascending=False)
          .head(10)
          .reset_index()
          .rename(columns={0: 'playcount'})
          .to_dict('records')
    )
    filtered_top_albums = (
        df.groupby(['album', 'artist']).size()
          .sort_values(ascending=False)
          .head(10)
          .reset_index()
          .rename(columns={0: 'playcount'})
          .to_dict('records')
    )

    return {
        **data,
        'df':              df,
        'top_artists':     filtered_top_artists,
        'top_tracks':      filtered_top_tracks,
        'top_albums':      filtered_top_albums,
        'total_scrobbles': len(df),
        'listening_hours': round(len(df) * 3.5 / 60, 1),
    }


# ------------------------------------------------------------------
# Post style defaults
# ------------------------------------------------------------------

DEFAULT_STYLE = {
    'show_counts':    True,   # include play counts
    'show_emojis':    True,   # include emoji decorations
    'top_n':          5,      # how many entries per section
    'sections':       ['artists', 'tracks', 'albums'],  # which sections to include
    'hashtags':       '#lastfm #scrobbleforge',
    'custom_intro':   '',     # optional custom intro line
}


# ------------------------------------------------------------------
# Post formatters
# ------------------------------------------------------------------

def _truncate(text: str, limit: int = BLUESKY_LIMIT) -> str:
    return text if len(text) <= limit else text[:limit - 1] + '\u2026'


def format_header_post(data: dict, style: dict = None) -> str:
    s = {**DEFAULT_STYLE, **(style or {})}
    period_label = 'Weekly' if data['period'] == 'weekly' else 'Monthly'
    now = datetime.now()
    days = 7 if data['period'] == 'weekly' else 30
    start = now - timedelta(days=days)
    date_range = f"{start.strftime('%b')} {start.day} \u2013 {now.strftime('%b')} {now.day}, {now.year}"

    emoji = '\U0001f3b5 ' if s['show_emojis'] else ''
    intro = s['custom_intro'] + '\n' if s['custom_intro'] else ''
    counts = f"{data['total_scrobbles']} scrobbles | ~{data['listening_hours']} hrs\n" if s['show_counts'] else ''
    text = (
        f"{emoji}{intro}{period_label} Digest for {data['username']}\n"
        f"{date_range}\n\n"
        f"{counts}"
        f"{s['hashtags']}"
    )
    return _truncate(text)


def format_top_artists_post(data: dict, style: dict = None) -> str:
    s = {**DEFAULT_STYLE, **(style or {})}
    emoji = '\U0001f3a4 ' if s['show_emojis'] else ''
    lines = [f"{emoji}Top Artists"]
    for i, a in enumerate(data['top_artists'][:s['top_n']], 1):
        name = a.get('name') or a.get('artist', '')
        count = a.get('playcount', 0)
        count_str = f" \u2014 {count}" if s['show_counts'] else ''
        lines.append(f"{i}. {name}{count_str}")
    return _truncate('\n'.join(lines))


def format_top_tracks_post(data: dict, style: dict = None) -> str:
    s = {**DEFAULT_STYLE, **(style or {})}
    emoji = '\U0001f3b6 ' if s['show_emojis'] else ''
    lines = [f"{emoji}Top Tracks"]
    for i, t in enumerate(data['top_tracks'][:s['top_n']], 1):
        name   = t.get('name', '') or t.get('track', '')
        artist = t.get('artist', '')
        count  = t.get('playcount', 0)
        count_str = f" ({count})" if s['show_counts'] else ''
        lines.append(f"{i}. {name} \u2014 {artist}{count_str}")
    return _truncate('\n'.join(lines))


def format_top_albums_post(data: dict, style: dict = None) -> str:
    s = {**DEFAULT_STYLE, **(style or {})}
    emoji = '\U0001f4bf ' if s['show_emojis'] else ''
    lines = [f"{emoji}Top Albums"]
    for i, a in enumerate(data['top_albums'][:s['top_n']], 1):
        name   = a.get('name', '') or a.get('album', '')
        artist = a.get('artist', '')
        count  = a.get('playcount', 0)
        count_str = f" ({count})" if s['show_counts'] else ''
        lines.append(f"{i}. {name} \u2014 {artist}{count_str}")
    return _truncate('\n'.join(lines))


def build_thread_posts(data: dict, style: dict = None) -> list:
    """Returns list of Bluesky post strings forming a thread, shaped by style options."""
    s = {**DEFAULT_STYLE, **(style or {})}
    posts = [format_header_post(data, s)]
    if 'artists' in s['sections']:
        posts.append(format_top_artists_post(data, s))
    if 'tracks' in s['sections']:
        posts.append(format_top_tracks_post(data, s))
    if 'albums' in s['sections']:
        posts.append(format_top_albums_post(data, s))
    return posts
