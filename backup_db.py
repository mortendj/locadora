# backup_db.py — CLI for db.py's backup/recovery functions.
#
# Usage:
#     python backup_db.py backup
#     python backup_db.py restore <path-to-snapshot.json>

import sys
from datetime import datetime
from pathlib import Path

import db

SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


def backup() -> None:
    SNAPSHOTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # DB_PATH.stem (e.g. "contracter" vs "contracter_demo") in the filename
    # both avoids same-second collisions between the two databases and
    # makes it obvious which database a given backup file came from.
    path = SNAPSHOTS_DIR / f"{db.DB_PATH.stem}_{timestamp}.json"
    print(f"Backing up: {db.DB_PATH}")
    db.export_snapshot(path)
    print(f"Backup written to {path}")
    print("Copy this file somewhere outside this machine to keep it safe.")


def restore(path_str: str) -> None:
    path = Path(path_str)
    if not path.exists():
        print(f"ERROR: {path} not found")
        sys.exit(1)

    answer = input(
        f"This will ERASE the current database ({db.DB_PATH}) and replace "
        f"it with the contents of {path}. Type 'yes' to continue: "
    )
    if answer.strip().lower() != "yes":
        print("Aborted — database left unchanged.")
        sys.exit(1)

    db.import_snapshot(path)
    print(f"Database restored from {path}")


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "backup":
        backup()
    elif len(sys.argv) == 3 and sys.argv[1] == "restore":
        restore(sys.argv[2])
    else:
        print("Usage:")
        print("    python backup_db.py backup")
        print("    python backup_db.py restore <path-to-snapshot.json>")
        sys.exit(1)


if __name__ == "__main__":
    main()
