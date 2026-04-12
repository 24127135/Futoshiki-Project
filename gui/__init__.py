"""GUI package for the Futoshiki Tkinter application.

This package contains presentation-layer components only:
- Main window composition
- Puzzle grid rendering widget
- Control panel widget
- Theme configuration
"""

from .app import FutoshikiApp
from .control_panel import ControlPanel
from .grid_widget import FutoshikiGridWidget
from .theme import ThemeConfig

__all__ = [
    "FutoshikiApp",
    "ControlPanel",
    "FutoshikiGridWidget",
    "ThemeConfig",
]
