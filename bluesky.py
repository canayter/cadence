import os
from dotenv import load_dotenv

load_dotenv()

BLUESKY_HANDLE   = os.getenv("BLUESKY_HANDLE")
BLUESKY_APP_PASS = os.getenv("BLUESKY_APP_PASSWORD")


class BlueskyPoster:
    """
    Thin wrapper around atproto.Client for posting digest threads.
    """

    def __init__(self, handle: str = None, app_password: str = None):
        self.handle   = handle or BLUESKY_HANDLE
        self.app_pass = app_password or BLUESKY_APP_PASS
        self._client  = None

    def login(self) -> None:
        if not self.handle or not self.app_pass:
            raise ValueError(
                "BLUESKY_HANDLE and BLUESKY_APP_PASSWORD must be set in .env or passed directly."
            )
        from atproto import Client
        self._client = Client()
        self._client.login(self.handle, self.app_pass)

    def post_thread(self, posts: list) -> list:
        """
        Posts a list of strings as a reply chain (thread) on Bluesky.
        Returns list of post URIs.
        """
        if not self._client:
            self.login()

        from atproto import models

        uris       = []
        root_ref   = None
        parent_ref = None

        for i, text in enumerate(posts):
            if i == 0:
                response   = self._client.send_post(text=text)
                root_ref   = models.create_strong_ref(response)
                parent_ref = root_ref
            else:
                reply = models.AppBskyFeedPost.ReplyRef(root=root_ref, parent=parent_ref)
                response   = self._client.send_post(text=text, reply_to=reply)
                parent_ref = models.create_strong_ref(response)
            uris.append(response.uri)

        return uris

    def validate_posts(self, posts: list) -> list:
        """Returns list of validation error strings. Empty list means all OK."""
        errors = []
        for i, post in enumerate(posts, 1):
            if len(post) > 300:
                errors.append(f"Post {i} is {len(post)} chars (limit 300)")
        return errors
