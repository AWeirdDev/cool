import base64
import re
import time
import httpx


class Spotify:
    def __init__(self, *, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.expires = 0
        self.token = ""

    async def obtain_token(self):
        if time.time() < self.expires:
            return

        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "client_credentials",
                },
                headers={
                    "Authorization": f'Basic {base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()}',
                },
            )
            r.raise_for_status()
            data = r.json()
            self.token = data["access_token"]
            self.expires = data["expires_in"]

    async def get_playlist(self, url: str) -> dict:
        await self.obtain_token()
        id_ = re.findall(r"playlist/([\d\w]+)", url)[0]

        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"https://api.spotify.com/v1/playlists/{id_}",
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
            )
            r.raise_for_status()
            return r.json()

    async def get_track(self, url: str) -> dict:
        await self.obtain_token()
        id_ = re.findall(r"track/([\d\w]+)", url)[0]

        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"https://api.spotify.com/v1/tracks/{id_}",
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
            )
            r.raise_for_status()
            return r.json()
