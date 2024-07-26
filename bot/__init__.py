import gc
from . import hooks

del hooks
gc.collect()

from .core import bot  # noqa: E402

__all__ = ["bot"]
