import asyncio

from pytubefix import YouTube
from youtubesearchpython.__future__ import VideosSearch


def create_source(url: str) -> str:
    print(url)
    result = YouTube(url).streams.get_audio_only()
    assert result
    return result.url


async def acreate_source(url: str) -> str:
    return await asyncio.to_thread(create_source, url)


async def asearch(query: str) -> dict:
    vids = VideosSearch(query, limit=1)
    return (await vids.next())["result"][0]
