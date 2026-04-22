from __future__ import annotations

import sys
from pathlib import Path

# Run from project root with: python gui/GUI.py
# This file lives in gui/, so the project root is one level up.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from gui.app import FutoshikiApp


def main() -> None:
    app = FutoshikiApp()
    app.mainloop()


if __name__ == "__main__":
    main()
