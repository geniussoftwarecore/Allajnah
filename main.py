import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'complaints_backend'))

from src.main import app  # type: ignore

if __name__ == '__main__':
    app.run()
