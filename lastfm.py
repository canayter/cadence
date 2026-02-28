import requests
import hashlib
import time
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://ws.audioscrobbler.com/2.0/"
API_KEY = os.getenv("LASTFM_API_KEY", "e378145b1e2b44eb782e251f6baa2ff9")
API_SECRET = os.getenv("LASTFM_API_SECRET", "43aa6cccde0beba1f8deb9a09d0f5bda")
AVG_TRACK_MINUTES = 3.5


class LastFMClient:
    """
    Read-only Last.fm client. No session key required.
    Works entirely off public profile data using API key only.
    """

    def __init__(self, username: str):
        self.username = username
        self.api_key = API_KEY
        self.api_secret = API_SECRET
        self._tag_cache: dict = {}

    # ------------------------------------------------------------------
    # Reused verbatim from Last.fm Insights/lastfm-insights.py
    # ------------------------------------------------------------------

    def generate_api_signature(self, params: dict) -> str:
        """MD5 signature per Last.fm spec."""
        params_copy = params.copy()
        params_copy.pop('format', None)
        params_copy.pop('api_sig', None)
        sorted_params = sorted(params_copy.items())
        sig_str = ''.join(k + str(v) for k, v in sorted_params)
        sig_str += self.api_secret
        return hashlib.md5(sig_str.encode('utf-8')).hexdigest()

    def create_listening_df(self, raw_data: dict) -> pd.DataFrame:
        """Convert raw recenttracks JSON to enriched DataFrame."""
        tracks = []
        for track in raw_data['recenttracks']['track']:
            if '@attr' in track and track['@attr'].get('nowplaying'):
                continue
            tracks.append({
                'artist':    track['artist']['#text'],
                'album':     track['album']['#text'],
                'track':     track['name'],
                'timestamp': int(track['date']['uts']),
                'datetime':  datetime.fromtimestamp(int(track['date']['uts']))
            })
        df = pd.DataFrame(tracks)
        if df.empty:
            return df
        df['hour']       = df['datetime'].dt.hour
        df['day']        = df['datetime'].dt.day_name()
        df['month']      = df['datetime'].dt.month
        df['month_name'] = df['datetime'].dt.month_name()
        df['year']       = df['datetime'].dt.year
        df['season']     = df['datetime'].dt.month.map(
            lambda x: 'Winter' if x in [12, 1, 2] else
                      'Spring' if x in [3, 4, 5] else
                      'Summer' if x in [6, 7, 8] else 'Fall'
        )
        return df

    # ------------------------------------------------------------------
    # Period helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_period_timestamps(period: str) -> tuple:
        now = int(time.time())
        days = 7 if period == 'weekly' else 30
        return now - days * 24 * 60 * 60, now

    @staticmethod
    def period_to_lastfm_str(period: str) -> str:
        return '7day' if period == 'weekly' else '1month'

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------

    def fetch_recent_tracks(self, period: str = 'weekly') -> dict:
        """Paginated fetch of user.getrecenttracks for the given period."""
        from_ts, to_ts = self.get_period_timestamps(period)
        all_tracks = []
        page = 1
        total_pages = 1
        last_attr = {}

        while page <= total_pages:
            params = {
                'method':  'user.getrecenttracks',
                'user':    self.username,
                'api_key': self.api_key,
                'format':  'json',
                'limit':   200,
                'page':    page,
                'from':    from_ts,
                'to':      to_ts,
            }
            resp = requests.get(BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            if 'error' in data:
                raise ValueError(f"Last.fm API error {data['error']}: {data.get('message', '')}")
            last_attr = data['recenttracks'].get('@attr', {})
            total_pages = int(last_attr.get('totalPages', 1))
            tracks = data['recenttracks']['track']
            if isinstance(tracks, dict):
                tracks = [tracks]
            all_tracks.extend(tracks)
            page += 1

        return {'recenttracks': {'track': all_tracks, '@attr': last_attr}}

    def fetch_top_artists(self, period: str = 'weekly', limit: int = 10) -> list:
        params = {
            'method':  'user.gettopartists',
            'user':    self.username,
            'api_key': self.api_key,
            'format':  'json',
            'period':  self.period_to_lastfm_str(period),
            'limit':   limit,
        }
        resp = requests.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        if 'error' in data:
            raise ValueError(f"Last.fm API error {data['error']}: {data.get('message', '')}")
        return [
            {'name': a['name'], 'playcount': int(a['playcount'])}
            for a in data['topartists']['artist']
        ]

    def fetch_top_tracks(self, period: str = 'weekly', limit: int = 10) -> list:
        params = {
            'method':  'user.gettoptracks',
            'user':    self.username,
            'api_key': self.api_key,
            'format':  'json',
            'period':  self.period_to_lastfm_str(period),
            'limit':   limit,
        }
        resp = requests.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        if 'error' in data:
            raise ValueError(f"Last.fm API error {data['error']}: {data.get('message', '')}")
        return [
            {
                'name':      t['name'],
                'artist':    t['artist']['name'],
                'playcount': int(t['playcount'])
            }
            for t in data['toptracks']['track']
        ]

    def fetch_top_albums(self, period: str = 'weekly', limit: int = 10) -> list:
        params = {
            'method':  'user.gettopalbums',
            'user':    self.username,
            'api_key': self.api_key,
            'format':  'json',
            'period':  self.period_to_lastfm_str(period),
            'limit':   limit,
        }
        resp = requests.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
        if 'error' in data:
            raise ValueError(f"Last.fm API error {data['error']}: {data.get('message', '')}")
        return [
            {
                'name':      a['name'],
                'artist':    a['artist']['name'],
                'playcount': int(a['playcount'])
            }
            for a in data['topalbums']['album']
        ]

    # ------------------------------------------------------------------
    # Genre / tag enrichment
    # ------------------------------------------------------------------

    def fetch_artist_tags(self, artist_name: str, top_n: int = 3) -> list:
        """Get top tags for an artist. Results cached per instance."""
        if artist_name in self._tag_cache:
            return self._tag_cache[artist_name]
        params = {
            'method':  'artist.gettoptags',
            'artist':  artist_name,
            'api_key': self.api_key,
            'format':  'json',
        }
        try:
            resp = requests.get(BASE_URL, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            tags = [t['name'].lower() for t in data.get('toptags', {}).get('tag', [])[:top_n]]
        except Exception:
            tags = []
        self._tag_cache[artist_name] = tags
        return tags

    def enrich_df_with_tags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add a 'tags' column (list[str]) to the scrobble DataFrame."""
        if df.empty:
            df = df.copy()
            df['tags'] = []
            return df
        unique_artists = df['artist'].unique()
        tag_map = {artist: self.fetch_artist_tags(artist) for artist in unique_artists}
        df = df.copy()
        df['tags'] = df['artist'].map(tag_map)
        return df

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def get_digest_data(self, period: str = 'weekly') -> dict:
        """
        Fetches everything needed for a digest.
        Returns a bundle dict consumed by digest.py.
        """
        raw = self.fetch_recent_tracks(period)
        df = self.create_listening_df(raw)
        df = self.enrich_df_with_tags(df)

        total_scrobbles = len(df)
        listening_hours = round(total_scrobbles * AVG_TRACK_MINUTES / 60, 1)

        return {
            'period':          period,
            'username':        self.username,
            'df':              df,
            'top_artists':     self.fetch_top_artists(period),
            'top_tracks':      self.fetch_top_tracks(period),
            'top_albums':      self.fetch_top_albums(period),
            'total_scrobbles': total_scrobbles,
            'listening_hours': listening_hours,
        }
