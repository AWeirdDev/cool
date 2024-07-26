from typing import List

import httpx


async def fetch_lyrics(query: str) -> list:
    client = httpx.AsyncClient(verify=False)

    r = await client.get("https://api.textyl.co/api/lyrics", params={"q": query})
    r.raise_for_status()

    return r.json()


def merge_lyric_timings(lyrics: List[dict]):
    merges = []
    counter = 0
    texts = []
    last_ts = 0

    for item in lyrics:
        counter += item["seconds"] - last_ts
        texts.append(item["lyrics"])

        last_ts = item["seconds"]

        if counter > 8.0:
            merges.append((counter, texts))
            texts = []
            counter = 0

    if texts:
        merges.append((0, texts))

    return merges
