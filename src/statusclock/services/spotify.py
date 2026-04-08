"""Spotify integration for fetching currently playing track."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import spotipy
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError

from ..i18n import I18N

SCOPE = "user-read-currently-playing user-read-playback-state"


@dataclass(slots=True)
class SpotifySnapshot:
    """Snapshot of the current Spotify playback state."""

    title: str
    artist: str
    is_playing: bool
    album_art_url: str | None


class SpotifyService:
    """Fetches current playback info from Spotify."""

    def __init__(
        self,
        *,
        client_id: str | None,
        client_secret: str | None,
        redirect_uri: str | None,
        cache_path: Path,
        i18n: I18N,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.cache_path = cache_path
        self.i18n = i18n
        self._auth_manager: SpotifyOAuth | None = None
        self._client: spotipy.Spotify | None = None

    def is_configured(self) -> bool:
        """Check if Spotify credentials are set."""
        return all([self.client_id, self.client_secret, self.redirect_uri])

    def fetch(self) -> SpotifySnapshot:
        """Fetch current playback state from Spotify."""
        if not self.is_configured():
            raise RuntimeError(self.i18n.t("spotify_missing_config"))

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            client = self._get_client()
            playback = client.current_playback(additional_types="track")
            if not playback:
                playback = client.current_user_playing_track()
        except SpotifyOauthError as exc:
            raise RuntimeError(self.i18n.t("spotify_auth_error")) from exc
        except SpotifyException as exc:
            raise RuntimeError(self.i18n.t("spotify_api_error", message=exc.msg)) from exc

        if not playback:
            return SpotifySnapshot(
                title=self.i18n.t("spotify_no_playback_title"),
                artist=self.i18n.t("spotify_no_playback_artist"),
                is_playing=False,
                album_art_url=None,
            )

        item = playback.get("item") or {}
        artists = item.get("artists") or []
        artist_names = ", ".join(artist["name"] for artist in artists) or self.i18n.t("spotify_unknown_artist")
        title = item.get("name") or self.i18n.t("spotify_unknown_track")
        images = (item.get("album") or {}).get("images") or []
        album_art_url = images[1]["url"] if len(images) > 1 else (images[0]["url"] if images else None)

        return SpotifySnapshot(
            title=title,
            artist=artist_names,
            is_playing=bool(playback.get("is_playing")),
            album_art_url=album_art_url,
        )

    def _get_client(self) -> spotipy.Spotify:
        """Get or create authenticated Spotify client."""
        if self._client is not None:
            return self._client

        self._auth_manager = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=SCOPE,
            open_browser=True,
            cache_path=str(self.cache_path),
            show_dialog=False,
        )
        self._client = spotipy.Spotify(auth_manager=self._auth_manager)
        return self._client
