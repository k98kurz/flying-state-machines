from __future__ import annotations
import importlib.metadata


__version__ = importlib.metadata.version('flying-state-machines')

def version() -> str:
    """Return the current library version."""
    return __version__

