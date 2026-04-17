import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from gui.app import FutoshikiApp

if __name__ == "__main__":
    app = FutoshikiApp()
    app.mainloop()
