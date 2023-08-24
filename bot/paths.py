from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent

SETTINGS_DIR = BASE_DIR / "settings"
CONFIG_DIR = BASE_DIR / "config"
INPUT_DIR  = BASE_DIR / "input"
LOG_DIR    = BASE_DIR / "log"

DIRS = [INPUT_DIR, LOG_DIR]

for dirpath in DIRS:
    dirpath.mkdir(exist_ok=True)
