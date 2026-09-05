from __future__ import annotations

import shutil

from database import DB, STORAGE_DIR, initialize_database, seed_demo_documents
from auth import seed_demo_users


if DB.exists():
    DB.unlink()

if STORAGE_DIR.exists():
    shutil.rmtree(STORAGE_DIR)

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
initialize_database()
seed_demo_users()
seed_demo_documents()
print("LandVerify demo database reset successfully.")
