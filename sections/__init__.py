# sections/__init__.py
from .inspector import render_inspector
from .controls import render_controls
from .history import render_history

__all__ = [
    "render_inspector",
    "render_controls",
    "render_history",
]
