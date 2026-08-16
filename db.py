# db.py — sqlite repository layer for Locadora.
#
# Every other module talks to the database only through the functions
# below — never through raw SQL or a sqlite3 connection directly. That
# keeps this file as the single swappable seam if the storage backend
# ever needs to change.
#
# Regular, always-queried-individually fields (a person's CPF, a
# property's address, a contract's rent) are plain columns. Fields that
# are only ever read/written as a whole blob (a property's inventory,
# a booking's configuration presets, witnesses) are stored as JSON text
# in a single column instead of being fully normalized — there's no
# query that needs to reach inside them.

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

# Two known database files: the real one (actual business data) and a
# demo one (the anonymized dataset — see seed_demo_data.py). Which
# one is active is controlled by the CONTRACTER_DB environment variable
# (a path, overriding the default entirely) — unset defaults to the demo
# database, so a plain `python main.py ...` during casual dev/testing
# can never touch real data by accident. Set CONTRACTER_DB explicitly
# (e.g. to REAL_DB_PATH's value) to work with real data on purpose.
REAL_DB_PATH = Path(__file__).parent / "contracter.db"
DEMO_DB_PATH = Path(__file__).parent / "contracter_demo.db"

DB_PATH = Path(os.environ["CONTRACTER_DB"]) if os.environ.get("CONTRACTER_DB") else DEMO_DB_PATH

# Every table that holds real rows, in FK-dependency order (a table only
# ever references a table earlier in this list). export_snapshot() dumps
# in this order; import_snapshot() deletes in reverse and re-inserts in
# this order.
_TABLES_IN_DEPENDENCY_ORDER = [
    ("people", "id"),
    ("properties", "id"),
    ("contracts", "id"),
    ("residential_contract_details", "contract_id"),
    ("short_term_contract_details", "contract_id"),
    ("commercial_contract_details", "contract_id"),
    ("contract_witnesses", "id"),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    type                TEXT NOT NULL DEFAULT 'individual',
    name                TEXT,
    company_name        TEXT,
    nationality         TEXT,
    marital_status      TEXT,
    occupation          TEXT,
    gender              TEXT,
    rg                  TEXT,
    cpf                 TEXT,
    cnpj                TEXT,
    full_address        TEXT,
    registered_address  TEXT,
    phone               TEXT,
    email               TEXT,
    bank                TEXT,
    branch              TEXT,
    account             TEXT,
    pix_key             TEXT,
    representative_id   INTEGER REFERENCES people(id)
);

CREATE TABLE IF NOT EXISTS properties (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    category                    TEXT,
    subtitle                   TEXT,
    type                        TEXT,
    street_address              TEXT,
    neighborhood                TEXT,
    city                        TEXT,
    state                       TEXT,
    zip_code                    TEXT,
    use                         TEXT,
    commercial_use_description  TEXT,
    parking_capacity            INTEGER,
    common_areas_json           TEXT,
    bedrooms_json                TEXT,
    configurations_json          TEXT,
    water_hazards_json           TEXT
);

CREATE TABLE IF NOT EXISTS contracts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_type  TEXT NOT NULL,
    landlord_id    INTEGER NOT NULL REFERENCES people(id),
    tenant_id      INTEGER NOT NULL REFERENCES people(id),
    guarantor_id   INTEGER REFERENCES people(id),
    property_id    INTEGER NOT NULL REFERENCES properties(id),
    contract_date  TEXT
);

CREATE TABLE IF NOT EXISTS residential_contract_details (
    contract_id              INTEGER PRIMARY KEY REFERENCES contracts(id),
    start_date               TEXT,
    term_months              INTEGER,
    term_months_spelled_out  TEXT,
    security_deposit_amount  TEXT,
    penalty_months           INTEGER,
    penalty_months_spelled_out TEXT,
    rent                     TEXT,
    due_day                  INTEGER,
    early_payment_discount   TEXT,
    initial_discount_months  INTEGER,
    initial_discount_amount  TEXT,
    property_tax_payer       TEXT
);

CREATE TABLE IF NOT EXISTS short_term_contract_details (
    contract_id                     INTEGER PRIMARY KEY REFERENCES contracts(id),
    check_in_date                   TEXT,
    check_in_time                   TEXT,
    check_out_date                  TEXT,
    check_out_time                  TEXT,
    max_guests                      INTEGER,
    configuration                   TEXT,
    total_amount                    TEXT,
    total_amount_spelled_out        TEXT,
    number_of_nights                INTEGER,
    nightly_rate                    TEXT,
    down_payment_amount             TEXT,
    balance_amount                  TEXT,
    balance_due_date                TEXT,
    cleaning_fee                    TEXT,
    utilities_included              INTEGER,
    extra_guest_fee_per_day         TEXT,
    security_deposit_amount         TEXT,
    allow_pets                      INTEGER,
    allow_buyer_showings             INTEGER,
    notice_days                     INTEGER,
    forfeit_percent_30_days_or_more  INTEGER,
    forfeit_percent_under_30_days    INTEGER
);

CREATE TABLE IF NOT EXISTS commercial_contract_details (
    contract_id                   INTEGER PRIMARY KEY REFERENCES contracts(id),
    start_date                    TEXT,
    term_months                   INTEGER,
    term_months_spelled_out       TEXT,
    rent                          TEXT,
    due_day                       INTEGER,
    security_deposit_amount       TEXT,
    initial_discount_amount       TEXT,
    initial_discount_months       INTEGER,
    penalty_months                INTEGER,
    penalty_months_spelled_out    TEXT,
    property_tax_payer            TEXT,
    late_payment_penalty_percent  REAL,
    extra_json                    TEXT
);

CREATE TABLE IF NOT EXISTS contract_witnesses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id  INTEGER NOT NULL REFERENCES contracts(id),
    position     INTEGER NOT NULL,
    name         TEXT,
    cpf          TEXT
);
"""

_conn = None


def get_connection():
    """Module-level sqlite3 connection, opened lazily on first use."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


def init_db():
    """Create all tables if they don't already exist. Safe to call repeatedly."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()


def close():
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def use_database(path) -> None:
    """
    Explicitly point at a different database file, closing any
    already-open connection first. Lets a script pick a database
    regardless of CONTRACTER_DB — e.g. seed_demo_data.py always
    targets DEMO_DB_PATH even if CONTRACTER_DB is set to the real one.
    """
    global DB_PATH
    close()
    DB_PATH = Path(path)


# ── People ───────────────────────────────────────────────────────────────────

def insert_person(data: dict) -> int:
    """
    Insert a person (individual or company). If data contains a
    "representative" dict (a company's legal representative), that person
    is inserted first and linked via representative_id.
    """
    conn = get_connection()

    representative_id = None
    representative = data.get("representative")
    if representative:
        representative_id = insert_person(representative)

    bank_details = data.get("bank_details") or {}

    cur = conn.execute(
        """
        INSERT INTO people (
            type, name, company_name, nationality, marital_status,
            occupation, gender, rg, cpf, cnpj, full_address,
            registered_address, phone, email, bank, branch, account,
            pix_key, representative_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("type", "individual"),
            data.get("name"),
            data.get("company_name"),
            data.get("nationality"),
            data.get("marital_status"),
            data.get("occupation"),
            data.get("gender"),
            data.get("rg"),
            data.get("cpf"),
            data.get("cnpj"),
            data.get("full_address"),
            data.get("registered_address"),
            data.get("phone"),
            data.get("email"),
            bank_details.get("bank"),
            bank_details.get("branch"),
            bank_details.get("account"),
            bank_details.get("pix_key"),
            representative_id,
        ),
    )
    conn.commit()
    return cur.lastrowid


def get_person(person_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
    if row is None:
        return None
    return _person_row_to_dict(row)


def list_people() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM people ORDER BY id").fetchall()
    return [_person_row_to_dict(row) for row in rows]


def _person_row_to_dict(row: sqlite3.Row) -> dict:
    person = {
        "id":                 row["id"],
        "type":               row["type"],
        "name":               row["name"],
        "company_name":       row["company_name"],
        "nationality":        row["nationality"],
        "marital_status":     row["marital_status"],
        "occupation":         row["occupation"],
        "gender":             row["gender"],
        "rg":                 row["rg"],
        "cpf":                row["cpf"],
        "cnpj":               row["cnpj"],
        "full_address":       row["full_address"],
        "registered_address": row["registered_address"],
        "phone":              row["phone"],
        "email":              row["email"],
    }
    if row["bank"] or row["branch"] or row["account"] or row["pix_key"]:
        person["bank_details"] = {
            "bank":    row["bank"],
            "branch":  row["branch"],
            "account": row["account"],
            "pix_key": row["pix_key"],
        }
    if row["representative_id"] is not None:
        person["representative"] = get_person(row["representative_id"])
    return person


# ── Properties ───────────────────────────────────────────────────────────────

def insert_property(data: dict) -> int:
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO properties (
            category, subtitle, type, street_address, neighborhood, city,
            state, zip_code, use, commercial_use_description,
            parking_capacity, common_areas_json, bedrooms_json,
            configurations_json, water_hazards_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("category"),
            data.get("subtitle"),
            data.get("type"),
            data.get("street_address"),
            data.get("neighborhood"),
            data.get("city"),
            data.get("state"),
            data.get("zip_code"),
            data.get("use"),
            data.get("commercial_use_description"),
            data.get("parking_capacity"),
            _dump_json(data.get("common_areas")),
            _dump_json(data.get("bedrooms")),
            _dump_json(data.get("configurations")),
            _dump_json(data.get("water_hazards")),
        ),
    )
    conn.commit()
    return cur.lastrowid


def get_property(property_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM properties WHERE id = ?", (property_id,)
    ).fetchone()
    if row is None:
        return None
    return _property_row_to_dict(row)


def list_properties() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM properties ORDER BY id").fetchall()
    return [_property_row_to_dict(row) for row in rows]


def _property_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id":                          row["id"],
        "category":                    row["category"],
        "subtitle":                    row["subtitle"],
        "type":                        row["type"],
        "street_address":              row["street_address"],
        "neighborhood":                row["neighborhood"],
        "city":                        row["city"],
        "state":                       row["state"],
        "zip_code":                    row["zip_code"],
        "use":                         row["use"],
        "commercial_use_description":  row["commercial_use_description"],
        "parking_capacity":            row["parking_capacity"],
        "common_areas":                _load_json(row["common_areas_json"]),
        "bedrooms":                    _load_json(row["bedrooms_json"]),
        "configurations":              _load_json(row["configurations_json"]),
        "water_hazards":               _load_json(row["water_hazards_json"]),
    }


# ── Contracts ────────────────────────────────────────────────────────────────

_RESIDENTIAL_DETAIL_FIELDS = [
    "start_date", "term_months", "term_months_spelled_out",
    "security_deposit_amount", "penalty_months", "penalty_months_spelled_out",
    "rent", "due_day", "early_payment_discount", "initial_discount_months",
    "initial_discount_amount", "property_tax_payer",
]

_SHORT_TERM_DETAIL_FIELDS = [
    "check_in_date", "check_in_time", "check_out_date", "check_out_time",
    "max_guests", "configuration", "total_amount", "total_amount_spelled_out",
    "number_of_nights", "nightly_rate", "down_payment_amount",
    "balance_amount", "balance_due_date", "cleaning_fee",
    "utilities_included", "extra_guest_fee_per_day", "security_deposit_amount",
    "allow_pets", "allow_buyer_showings", "notice_days",
    "forfeit_percent_30_days_or_more", "forfeit_percent_under_30_days",
]

# "extra_json" bundles the handful of fields that are only ever rendered
# whole into one specific clause and never queried/filtered on
# individually (renovation reimbursement figures, property registration,
# a tenant's professional-council registration, the optional
# space-sharing carve-out, the early-termination penalty formula
# override). Everything else here already exists as a plain column on
# residential_contract_details and is reused with the same name/shape.
_COMMERCIAL_DETAIL_FIELDS = [
    "start_date", "term_months", "term_months_spelled_out", "rent", "due_day",
    "security_deposit_amount", "initial_discount_amount", "initial_discount_months",
    "penalty_months", "penalty_months_spelled_out", "property_tax_payer",
    "late_payment_penalty_percent", "extra_json",
]


def insert_contract(
    contract_type: str,
    landlord_id: int,
    tenant_id: int,
    property_id: int,
    contract_date: str,
    details: dict,
    guarantor_id: int | None = None,
    witnesses: list[dict] | None = None,
) -> int:
    """
    contract_type: "residential", "short_term", or "commercial".
    details: the type-specific fields (see _RESIDENTIAL_DETAIL_FIELDS /
        _SHORT_TERM_DETAIL_FIELDS / _COMMERCIAL_DETAIL_FIELDS) — unknown/missing
        keys default to None. For "commercial", pass a nested dict under
        details["extra"] (not details["extra_json"]) for the JSON-blob
        fields (renovation_description, renovation_total_cost,
        renovation_total_cost_spelled_out, registration_number,
        registry_office, professional_registration_label,
        professional_registration_number, penalty_formula,
        sharing_allowed, sharing_description) — it's dumped to JSON here,
        same as insert_property() does for its list/dict fields.
    """
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO contracts (
            contract_type, landlord_id, tenant_id, guarantor_id,
            property_id, contract_date
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (contract_type, landlord_id, tenant_id, guarantor_id, property_id, contract_date),
    )
    contract_id = cur.lastrowid

    if contract_type == "residential":
        fields = _RESIDENTIAL_DETAIL_FIELDS
        table = "residential_contract_details"
    elif contract_type == "short_term":
        fields = _SHORT_TERM_DETAIL_FIELDS
        table = "short_term_contract_details"
    elif contract_type == "commercial":
        fields = _COMMERCIAL_DETAIL_FIELDS
        table = "commercial_contract_details"
    else:
        raise ValueError(f"Unknown contract_type: {contract_type!r}")

    placeholders = ", ".join("?" for _ in fields)
    columns = ", ".join(fields)
    values = [
        _dump_json(details.get("extra")) if f == "extra_json" else details.get(f)
        for f in fields
    ]
    conn.execute(
        f"INSERT INTO {table} (contract_id, {columns}) VALUES (?, {placeholders})",
        (contract_id, *values),
    )

    for i, witness in enumerate(witnesses or []):
        conn.execute(
            "INSERT INTO contract_witnesses (contract_id, position, name, cpf) "
            "VALUES (?, ?, ?, ?)",
            (contract_id, i, witness.get("name"), witness.get("cpf")),
        )

    conn.commit()
    return contract_id


def get_contract(contract_id: int) -> dict | None:
    """
    Reconstructs the same nested dict shape main.py's contract modules
    produce today (landlord/tenant/guarantor/property embedded, plus
    dates/pricing/termination/charges for residential or
    stay/pricing/termination/rules/security_deposit for short_term) — so
    this can act as a drop-in replacement for `contract_module.data`.
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
    if row is None:
        return None

    data = {
        "contract_type": row["contract_type"],
        "landlord":      get_person(row["landlord_id"]),
        "tenant":        get_person(row["tenant_id"]),
        "guarantor":     get_person(row["guarantor_id"]) if row["guarantor_id"] else None,
        "property":      get_property(row["property_id"]),
        "contract":      {"date": row["contract_date"]},
    }

    if row["contract_type"] == "residential":
        details = conn.execute(
            "SELECT * FROM residential_contract_details WHERE contract_id = ?",
            (contract_id,),
        ).fetchone()
        data["dates"] = {
            "start_date":              details["start_date"],
            "term_months":             details["term_months"],
            "term_months_spelled_out": details["term_months_spelled_out"],
        }
        data["security_deposit"] = {"amount": details["security_deposit_amount"]}
        data["termination"] = {
            "penalty_months":             details["penalty_months"],
            "penalty_months_spelled_out": details["penalty_months_spelled_out"],
        }
        data["pricing"] = {
            "rent":                    details["rent"],
            "due_day":                 details["due_day"],
            "early_payment_discount":  details["early_payment_discount"],
            "initial_discount_months": details["initial_discount_months"],
            "initial_discount_amount": details["initial_discount_amount"],
        }
        data["charges"] = {"property_tax_payer": details["property_tax_payer"]}

    elif row["contract_type"] == "short_term":
        details = conn.execute(
            "SELECT * FROM short_term_contract_details WHERE contract_id = ?",
            (contract_id,),
        ).fetchone()
        data["stay"] = {
            "check_in_date":  details["check_in_date"],
            "check_in_time":  details["check_in_time"],
            "check_out_date": details["check_out_date"],
            "check_out_time": details["check_out_time"],
            "max_guests":     details["max_guests"],
            "configuration":  details["configuration"],
        }
        data["pricing"] = {
            "total_amount":             details["total_amount"],
            "total_amount_spelled_out": details["total_amount_spelled_out"],
            "number_of_nights":         details["number_of_nights"],
            "nightly_rate":             details["nightly_rate"],
            "down_payment_amount":      details["down_payment_amount"],
            "balance_amount":           details["balance_amount"],
            "balance_due_date":         details["balance_due_date"],
            "cleaning_fee":             details["cleaning_fee"],
            "utilities_included":      bool(details["utilities_included"]) if details["utilities_included"] is not None else None,
            "extra_guest_fee_per_day":  details["extra_guest_fee_per_day"],
        }
        data["security_deposit"] = {"amount": details["security_deposit_amount"]}
        data["rules"] = {
            "allow_pets":           bool(details["allow_pets"]) if details["allow_pets"] is not None else None,
            "allow_buyer_showings": bool(details["allow_buyer_showings"]) if details["allow_buyer_showings"] is not None else None,
        }
        data["termination"] = {
            "notice_days":                       details["notice_days"],
            "forfeit_percent_30_days_or_more":    details["forfeit_percent_30_days_or_more"],
            "forfeit_percent_under_30_days":      details["forfeit_percent_under_30_days"],
        }
        witnesses = conn.execute(
            "SELECT name, cpf FROM contract_witnesses WHERE contract_id = ? ORDER BY position",
            (contract_id,),
        ).fetchall()
        if witnesses:
            data["witnesses"] = [{"name": w["name"], "cpf": w["cpf"]} for w in witnesses]

    elif row["contract_type"] == "commercial":
        details = conn.execute(
            "SELECT * FROM commercial_contract_details WHERE contract_id = ?",
            (contract_id,),
        ).fetchone()
        extra = _load_json(details["extra_json"]) or {}
        data["dates"] = {
            "start_date":              details["start_date"],
            "term_months":             details["term_months"],
            "term_months_spelled_out": details["term_months_spelled_out"],
        }
        data["pricing"] = {
            "rent":                          details["rent"],
            "due_day":                       details["due_day"],
            "initial_discount_amount":       details["initial_discount_amount"],
            "initial_discount_months":       details["initial_discount_months"],
            "late_payment_penalty_percent":  details["late_payment_penalty_percent"],
        }
        data["security_deposit"] = {"amount": details["security_deposit_amount"]}
        data["termination"] = {
            "penalty_months":             details["penalty_months"],
            "penalty_months_spelled_out": details["penalty_months_spelled_out"],
            "penalty_formula":            extra.get("penalty_formula"),
        }
        data["charges"] = {"property_tax_payer": details["property_tax_payer"]}
        data["renovation"] = {
            "total_cost":             extra.get("renovation_total_cost"),
            "total_cost_spelled_out": extra.get("renovation_total_cost_spelled_out"),
            "description":            extra.get("renovation_description"),
        }
        data["registration"] = {
            "number":          extra.get("registration_number"),
            "registry_office": extra.get("registry_office"),
        }
        data["professional_registration"] = {
            "label":  extra.get("professional_registration_label"),
            "number": extra.get("professional_registration_number"),
        }
        data["sharing"] = {
            "allowed":     bool(extra.get("sharing_allowed")),
            "description": extra.get("sharing_description"),
        }

    return data


def list_contracts() -> list[dict]:
    """
    Lightweight summary rows for browsing/identifying contracts — id,
    type, tenant name, property address, the relevant start date, and a
    "label" string (tenant name / street address / start date) derived
    fresh from those columns every call. The label is for humans reading
    a listing, never stored, and never accepted as a lookup key — running
    a contract through main.py is always by numeric id.
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT
            c.id, c.contract_type, c.contract_date,
            COALESCE(t.name, t.company_name) AS tenant_name,
            p.street_address,
            COALESCE(r.start_date, st.check_in_date, m.start_date) AS start_date
        FROM contracts c
        JOIN people t ON t.id = c.tenant_id
        JOIN properties p ON p.id = c.property_id
        LEFT JOIN residential_contract_details r ON r.contract_id = c.id
        LEFT JOIN short_term_contract_details st ON st.contract_id = c.id
        LEFT JOIN commercial_contract_details m ON m.contract_id = c.id
        ORDER BY c.id
        """
    ).fetchall()

    contracts = []
    for row in rows:
        contract = dict(row)
        contract["label"] = f"{row['tenant_name']} / {row['street_address']} / {row['start_date']}"
        contracts.append(contract)
    return contracts


def update_commercial_details(contract_id: int, **fields) -> None:
    """
    Update one or more flat columns on commercial_contract_details — e.g.
    db.update_commercial_details(12, due_day=10). For the extra_json
    bundle's fields, use update_commercial_extra() instead.
    """
    if not fields:
        return
    conn = get_connection()
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(
        f"UPDATE commercial_contract_details SET {set_clause} WHERE contract_id = ?",
        (*fields.values(), contract_id),
    )
    conn.commit()


def update_commercial_extra(contract_id: int, **fields) -> None:
    """
    Merge one or more keys into commercial_contract_details.extra_json for
    the given contract — e.g. db.update_commercial_extra(12,
    registration_number="..."). Existing keys not passed are preserved.
    """
    conn = get_connection()
    row = conn.execute(
        "SELECT extra_json FROM commercial_contract_details WHERE contract_id = ?",
        (contract_id,),
    ).fetchone()
    extra = _load_json(row["extra_json"]) if row and row["extra_json"] else {}
    extra.update(fields)
    conn.execute(
        "UPDATE commercial_contract_details SET extra_json = ? WHERE contract_id = ?",
        (_dump_json(extra), contract_id),
    )
    conn.commit()


# ── JSON helpers ─────────────────────────────────────────────────────────────

def _dump_json(value):
    return json.dumps(value) if value is not None else None


def _load_json(value):
    return json.loads(value) if value is not None else None


# ── Backup / recovery ────────────────────────────────────────────────────────

def export_snapshot(path) -> None:
    """
    Dump every row of every table to a single human-readable JSON file —
    the real, storable-anywhere backup. Row IDs are preserved so
    import_snapshot() can restore the exact same relationships.
    """
    conn = get_connection()
    dump = {"exported_at": datetime.now().isoformat(), "tables": {}}
    for table, pk in _TABLES_IN_DEPENDENCY_ORDER:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY {pk}").fetchall()
        dump["tables"][table] = [dict(row) for row in rows]
    Path(path).write_text(
        json.dumps(dump, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def import_snapshot(path) -> None:
    """
    Fully replace the current database contents with what's in a snapshot
    file written by export_snapshot(). Erases whatever is currently in
    the database first — this is a full restore, not a merge.
    """
    dump = json.loads(Path(path).read_text(encoding="utf-8"))
    conn = get_connection()
    init_db()

    conn.execute("PRAGMA foreign_keys = OFF")
    for table, _ in reversed(_TABLES_IN_DEPENDENCY_ORDER):
        conn.execute(f"DELETE FROM {table}")
    for table, _ in _TABLES_IN_DEPENDENCY_ORDER:
        for row in dump["tables"].get(table, []):
            columns = ", ".join(row.keys())
            placeholders = ", ".join("?" for _ in row)
            conn.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                tuple(row.values()),
            )
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
