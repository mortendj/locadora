# Locadora

*"Locadora"* is Portuguese for a rental/leasing agency (as in *locadora de veículos*, a car rental company) — the name of the business this tool was built to serve, not just a label for the tool itself.

Generates Brazilian rental contracts — long-term residential and short-term (temporada) — as HTML and PDF, from a SQLite-backed data model.
Started as a tool to manage a small family rental business; the code and data here are a public, fully fictional demo of the same system.

## What it does

- Renders legally-structured lease agreements in Portuguese from structured Python/SQLite data, using Jinja2 templates.
- Three contract types today, each with its own template and validator: **long-term residential** leases, **short-term (temporada)** leases (capped at 90 days per Lei 8.245/91), and **commercial (non-residential)** leases — the last one built around opt-in modules (a renovation-reimbursement/rent-abatement deal, a professional-registration field, a space-sharing carve-out, a configurable early-termination penalty) so one template serves both a bare-bones lease and a heavily customized one.
- Every run produces four files: a clean HTML/PDF pair for signing, and a second HTML/PDF pair with every contract-specific field highlighted in red, for reviewing a draft before it goes out.
- Validators catch missing/inconsistent data before a document is ever rendered — errors block generation, warnings don't.
  Examples: a short-term stay over 90 days, a down payment that doesn't add up to the total.

## Quick start

```bash
pip install -r requirements.txt
python seed_demo_data.py    # populates contracter_demo.db from demo/
```

A contract can then be rendered two ways, and after seeding both point at the same demo data:

```bash
python main.py --list       # find the numeric id, then:
python main.py 1            # render by database id

# ...or render by fixture name — mirrors its path under demo/contracts/
python main.py real_estate.residential.long_term.elisa
```

Output lands in `output/` — `{name}_preview.html`, `{name}_review.html`, `{name}_locacao.pdf`, `{name}_review.pdf`.

## Backup & recovery

The database file itself (`contracter.db` for real data, `contracter_demo.db` for the demo dataset) is gitignored — git never backs it up, so once real data lives there it needs its own recovery path.

**Step 1 — back up:**

```bash
CONTRACTER_DB=/path/to/contracter.db python backup_db.py backup
```

Writes a timestamped, human-readable JSON snapshot of every table to `snapshots/` (also gitignored). Copy that file off-machine to actually be protected against losing this machine.

**Step 2 — restore:**

```bash
CONTRACTER_DB=/path/to/contracter.db python backup_db.py restore snapshots/contracter_<timestamp>.json
```

Erases whatever is currently in the target database and replaces it with the snapshot's contents — a full restore, not a merge — after a `yes` confirmation prompt.

Verified end-to-end 2026-08-16: backed up the real database, deleted the database file entirely to simulate total loss, restored from the snapshot, and confirmed every contract re-rendered identically to before.

## Design decisions worth knowing about

- **Demo data by default, real data only by explicit opt-in.** `db.py` picks its database file from the `CONTRACTER_DB` environment variable; unset, it falls back to `contracter_demo.db`.
  A plain `python main.py ...` can never touch a real, private database (e.g. `contracter.db`) by accident — that only happens if `CONTRACTER_DB` is set explicitly, on purpose.
  Both database files are gitignored; only the demo data seeded from `demo/` is ever tracked.

  To point at a real database instead, set the variable before running anything:

  ```bash
  CONTRACTER_DB=/path/to/contracter.db python main.py 8      # macOS/Linux/Git Bash
  ```

  ```powershell
  $env:CONTRACTER_DB = "C:\path\to\contracter.db"; python main.py 8   # Windows PowerShell
  ```
- **No ORM.** `db.py` is a thin repository layer over the stdlib `sqlite3` module — every other module talks to the database only through its functions, never through raw SQL directly.
  For a schema this size, direct SQL keeps exactly what's running fully visible and avoids ORM-generated query surprises.
  The repository module already gives the one swappable seam an ORM's data layer would, without the extra dependency.
- **Demo data is real code, not throwaway fixtures.** Everything under `demo/` is meant to stay readable and git-tracked permanently.
  It's both the test data and the documentation of what a valid contract dict looks like.
- **Two review passes per contract.** Rendering both a clean and a field-highlighted version from the same template means there's never a separate "review copy" to keep in sync with the real one.
  It's the exact same Jinja context with one flag flipped.
- **Directory structure mirrors the domain, not just the code.** Templates and demo contracts are organized by transaction type, country, asset class, and duration (`rental/brazil/real_estate/residential/{long_term,short_term}`).
  Those are the actual axes a new contract type would vary along, not implementation detail.

## Roadmap

- A read-only FastAPI viewer over the same database.
- Rental contract types beyond real estate (vehicles, equipment), and beyond Brazil.
  The data model was built with that in mind, though none of it exists yet.

## Tech stack

Python · Jinja2 · xhtml2pdf · SQLite (stdlib `sqlite3`, no ORM)

## License

MIT — see [LICENSE](LICENSE).
