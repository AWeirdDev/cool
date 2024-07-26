import asyncio
from dataclasses import dataclass
from typing import Dict, Optional

import discord

from .queue import Queue


@dataclass
class Client:
    vc: discord.VoiceClient
    queue: Queue
    player_progress_task: Optional[asyncio.Task] = None
    lyrics_task: Optional[asyncio.Task] = None
    lyrics_flags: Optional[asyncio.Event] = None
    player_message: Optional[discord.Message] = None


class Clients:
    clients: Dict[int, Client]

    def __init__(self):
        self.clients = {}

    def add(self, id: int, client: Client):
        self.clients[id] = client

    def remove(self, id: int):
        self.clients.pop(id)

    def get(self, id: int) -> Optional[Client]:
        return self.clients.get(id)
