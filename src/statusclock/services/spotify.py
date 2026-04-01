from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import spotipy
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyOauthError


SCOPE = "user-read-currently-playing user-read-playback-state"


@dataclass(slots=True)
class SpotifySnapshot:
    title: str
    artist: str
    is_playing: bool
    album_art_url: str | None


class SpotifyService:
    def __init__(
        self,
        *,
        client_id: str | None,
        client_secret: str | None,
        redirect_uri: str | None,
        cache_path: Path,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.cache_path = cache_path

    def is_configured(self) -> bool:
        return all([self.client_id, self.client_secret, self.redirect_uri])

    def fetch(self) -> SpotifySnapshot:
        if not self.is_configured():
            raise RuntimeError("Configura as variaveis SPOTIPY_CLIENT_ID/SECRET/REDIRECT_URI.")

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=SCOPE,
                open_browser=True,
                cache_path=str(self.cache_path),
                show_dialog=False,
            )
            client = spotipy.Spotify(auth_manager=auth_manager)
            playback = client.current_playback(additional_types="track")
            if not playback:
                playback = client.current_user_playing_track()
        except SpotifyOauthError as exc:
            raise RuntimeError(
                "Falha na autenticacao Spotify. Confirma client id, secret e redirect URI."
            ) from exc
        except SpotifyException as exc:
            raise RuntimeError(f"Erro Spotify: {exc.msg}") from exc

        if not playback:
            return SpotifySnapshot(
                title="Sem reprodução ativa",
                artist="Abre o Spotify para mostrar a música atual",
                is_playing=False,
                album_art_url=None,
            )

        item = playback.get("item") or {}
        artists = item.get("artists") or []
        artist_names = ", ".join(artist["name"] for artist in artists) or "Artista desconhecido"
        title = item.get("name") or "Faixa desconhecida"
        album = item.get("album") or {}
        images = album.get("images") or []
        album_art_url = images[1]["url"] if len(images) > 1 else (images[0]["url"] if images else None)

        return SpotifySnapshot(
            title=title,
            artist=artist_names,
            is_playing=bool(playback.get("is_playing")),
            album_art_url=album_art_url,
        )
