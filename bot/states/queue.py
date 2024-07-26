from dataclasses import dataclass
from typing import Any, List, Optional

import discord


@dataclass
class Canditate:
    source: discord.FFmpegPCMAudio
    title: str
    thumbnail: str
    query: str
    duration: str
    client: Optional[Any] = None
    linked_playlist: Optional[str] = None


class Queue:
    items: List[Canditate]

    def __init__(self):
        self.items = []

    def append(self, canditate: Canditate):
        self.items.append(canditate)

    def next(self) -> Optional[Canditate]:
        """Next item in queue.

        Returns None if queue is empty.
        """
        try:
            return self.items[0]
        except IndexError:
            return None

    def len(self) -> int:
        return len(self.items)

    def pop(self):
        if self.blank:
            return
        self.items.pop(0)

    @property
    def blank(self) -> bool:
        return not self.items
