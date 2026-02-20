"""Run the Lead Manager app: python -m lead_manager"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import app
import config

if __name__ == "__main__":
    print(f"\n  Lead Manager running at: http://localhost:{config.PORT}\n")
    app.run(host=config.HOST, port=config.PORT, debug=True)
