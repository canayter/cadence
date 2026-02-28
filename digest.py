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
# Post formatters
# ------------------------------------------------------------------

def _truncate(text: str, limit: int = BLUESKY_LIMIT) -> str:
    return text if len(text) <= limit else text[:limit - 1] + '\u2026'


def format_header_post(data: dict) -> str:
    period_label = 'Weekly' if data['period'] == 'weekly' else 'Monthly'
    now = datetime.now()
    days = 7 if data['period'] == 'weekly' else 30
    start = now - timedelta(days=days)
    date_range = f"{start.strftime('%b')} {start.day} \u2013 {now.strftime('%b')} {now.day}, {now.year}"

    text = (
        f"{period_label} Digest for {data['username']}\n"
        f"{date_range}\n\n"
        f"{data['total_scrobbles']} scrobbles | ~{data['listening_hours']} hrs\n"
        f"#lastfm #scrobbleforge"
    )
    return _truncate(text)


def format_top_artists_post(data: dict, top_n: int = 5) -> str:
    lines = ["Top Artists"]
    for i, a in enumerate(data['top_artists'][:top_n], 1):
        name = a.get('name') or a.get('artist', '')
        count = a.get('playcount', 0)
        lines.append(f"{i}. {name} \u2014 {count}")
    return _truncate('\n'.join(lines))


def format_top_tracks_post(data: dict, top_n: int = 5) -> str:
    lines = ["Top Tracks"]
    for i, t in enumerate(data['top_tracks'][:top_n], 1):
        name   = t.get('name', '') or t.get('track', '')
        artist = t.get('artist', '')
        count  = t.get('playcount', 0)
        lines.append(f"{i}. {name} \u2014 {artist} ({count})")
    return _truncate('\n'.join(lines))


def format_top_albums_post(data: dict, top_n: int = 5) -> str:
    lines = ["Top Albums"]
    for i, a in enumerate(data['top_albums'][:top_n], 1):
        name   = a.get('name', '') or a.get('album', '')
        artist = a.get('artist', '')
        count  = a.get('playcount', 0)
        lines.append(f"{i}. {name} \u2014 {artist} ({count})")
    return _truncate('\n'.join(lines))


def build_thread_posts(data: dict) -> list:
    """Returns list of 4 Bluesky post strings forming a thread."""
    return [
        format_header_post(data),
        format_top_artists_post(data),
        format_top_tracks_post(data),
        format_top_albums_post(data),
    ]
