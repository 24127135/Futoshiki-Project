from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    # When run as: python src/tools/gui_launcher.py
    # add the project root and src/ so both gui/ and futoshiki/ are importable.
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))

from gui.app import FutoshikiApp


def main() -> None:
    app = FutoshikiApp()
    app.mainloop()


if __name__ == "__main__":
    main()
