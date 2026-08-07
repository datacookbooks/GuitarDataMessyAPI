import os
import sqlite3
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent

# On Railway, use the attached persistent Volume.
# Locally, fall back to business_data.db in the repo folder.
volume_path = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")

if volume_path:
    DATABASE_PATH = Path(volume_path) / "business_data.db"
else:
    DATABASE_PATH = ROOT_DIR / "business_data.db"


def get_db_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(DATABASE_PATH),
        timeout=30
    )

    conn.row_factory = sqlite3.Row
    return conn
