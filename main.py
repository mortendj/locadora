# main.py

"""
main.py — Locadora entry point

Usage:
    python main.py 8                        (contract id — real contracts live in contracter.db)
    python main.py --list                    (list contract ids/labels in contracter.db)
    python main.py real_estate.residential.long_term.elisa   (demo/example fixtures — dotted module path)
    python main.py real_estate.residential.short_term.full_202608

Outputs per run (written to output/):
    {name}_preview.html   — clean
    {name}_review.html    — contract-specific fields in red
    {name}_locacao.pdf    — clean, for signing
    {name}_review.pdf     — highlighted, for review before signing
"""

import importlib
import math
import sys
from pathlib import Path

from dateutil.relativedelta import relativedelta
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from br_dates import parse_br_date, format_br_date
import db


# ── Paths ────────────────────────────────────────────────────────────────────

ROOT       = Path(__file__).parent
CSS_FILE   = ROOT / "templates" / "contract-legal.css"
OUTPUT_DIR = ROOT / "output"

# Registry of supported contract types. `data["contract_type"]` selects the
# entry; contracts that omit the key default to "residential" (the only type
# that existed before this registry, so existing contract files need no changes).
CONTRACT_TYPES = {
    "residential": {
        "template":        "rental/brazil/real_estate/residential/long_term/locacao.html",
        "validator_module": "templates.rental.brazil.real_estate.residential.long_term.locacao_validators",
        "validator_func":   "validate_locacao",
    },
    "seasonal": {
        "template":        "rental/brazil/real_estate/residential/short_term/locacao_temporada.html",
        "validator_module": "templates.rental.brazil.real_estate.residential.short_term.locacao_temporada_validators",
        "validator_func":   "validate_locacao_temporada",
    },
    "commercial": {
        "template":        "rental/brazil/real_estate/commercial/locacao_comercial.html",
        "validator_module": "templates.rental.brazil.real_estate.commercial.locacao_comercial_validators",
        "validator_func":   "validate_locacao_comercial",
    },
}


def _parse_brl(s: str) -> float:
    """Convert Brazilian currency string to float. e.g. '1.900,00' → 1900.0"""
    return float(s.replace(".", "").replace(",", "."))


# ── PDF writer ───────────────────────────────────────────────────────────────

def write_pdf(html_string: str, dest_path: Path) -> None:
    """Render html_string to PDF at dest_path via xhtml2pdf."""
    with open(dest_path, "wb") as fh:
        result = pisa.CreatePDF(html_string, dest=fh)
    if result.err:
        raise RuntimeError(
            f"xhtml2pdf reported {result.err} error(s) writing {dest_path}"
        )


# ── Rendering ────────────────────────────────────────────────────────────────

def build_context(data: dict, css: str, review_mode: bool) -> dict:
    """
    Flatten the contract data dict into the template context.
    All keys from data are passed through directly so the template
    can reference {{ landlord.name }}, {{ property.street_address }}, etc.
    review_mode and contract_css are injected on top.
    """
    return {
        **data,
        "contract_css": css,        # matches {{ contract_css }} in template
        "review_mode":  review_mode,
    }


def render_html(template, context: dict) -> str:
    return template.render(**context)


# ── Main ─────────────────────────────────────────────────────────────────────

def list_db_contracts() -> None:
    print(f"Database: {db.DB_PATH}")
    contracts = db.list_contracts()
    if not contracts:
        print("No contracts in the database yet.")
        return
    print(f"\n{'id':>4}  {'type':<12}  label")
    for c in contracts:
        print(f"{c['id']:>4}  {c['contract_type']:<12}  {c['label']}")
    print()


def main() -> None:

    # 1. Parse CLI argument
    if len(sys.argv) != 2:
        print("Usage: python main.py <contract_id | contract_name>")
        print("  e.g. python main.py 8   (contract id, reads from contracter.db)")
        print("  e.g. python main.py --list   (list contracts in contracter.db)")
        print("  e.g. python main.py real_estate.residential.long_term.elisa   (demo/example fixture)")
        sys.exit(1)

    arg = sys.argv[1].strip()

    if arg == "--list":
        list_db_contracts()
        return

    # 2. Load the contract's data — either a numeric database id, or (for
    #    demo/example fixtures that are meant to stay as literal, readable
    #    code) a dotted module path under demo.contracts.rental.brazil.
    if arg.isdigit():
        contract_id = int(arg)
        data: dict = db.get_contract(contract_id)
        if data is None:
            print(f"ERROR: No contract found in the database with id {contract_id}")
            sys.exit(1)
        contract_name = f"db{contract_id}"
    else:
        contract_name = arg
        module_path = f"demo.contracts.rental.brazil.{contract_name}"
        try:
            contract_module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            print(f"ERROR: Contract not found — {module_path}")
            sys.exit(1)
        data: dict = contract_module.data

    # 3. Resolve contract type
    contract_type_name = data.get("contract_type", "residential")
    contract_type = CONTRACT_TYPES.get(contract_type_name)
    if contract_type is None:
        print(f"ERROR: Unknown contract_type '{contract_type_name}'")
        sys.exit(1)

    # 4. Compute dates.end_date (residential/commercial — seasonal gives dates directly)
    if contract_type_name == "residential":
        start_date  = parse_br_date(data["dates"]["start_date"])
        term_months = data["dates"]["term_months"]
        end_date    = start_date + relativedelta(months=term_months)
        data["dates"]["end_date"] = format_br_date(end_date)
    elif contract_type_name == "commercial":
        dates_dict = data.get("dates", {})
        if dates_dict.get("start_date") and dates_dict.get("term_months"):
            start_date = parse_br_date(dates_dict["start_date"])
            end_date   = start_date + relativedelta(months=dates_dict["term_months"])
            dates_dict["end_date"] = format_br_date(end_date)

        pricing = data.setdefault("pricing", {})

        # Default late-payment fee when not set per-contract (see Cláusula
        # Terceira §2) — kept as a plain int when whole, to avoid rendering
        # "10.0%" for values that came back as a REAL column from sqlite.
        pct = pricing.get("late_payment_penalty_percent")
        if pct is None:
            pct = 10
        pricing["late_payment_penalty_percent"] = int(pct) if float(pct) == int(pct) else pct

        # Auto-derive the abatement period (months) from the renovation's
        # total cost and the fixed monthly credit, rather than asking for a
        # manually-estimated count that would go stale if the cost changes.
        renovation = data.get("renovation") or {}
        if renovation.get("total_cost") and pricing.get("initial_discount_amount"):
            monthly_credit = _parse_brl(pricing["initial_discount_amount"])
            if monthly_credit > 0:
                pricing["initial_discount_months"] = math.ceil(
                    _parse_brl(renovation["total_cost"]) / monthly_credit
                )
                # Exact resume-full-rent date, so Clause 4 §4 can state a date
                # instead of requiring a separate written-notice trigger event.
                if dates_dict.get("start_date"):
                    pricing["full_rent_start_date"] = format_br_date(
                        parse_br_date(dates_dict["start_date"])
                        + relativedelta(months=pricing["initial_discount_months"])
                    )

    # 5. Validate
    validator_module = importlib.import_module(contract_type["validator_module"])
    validate_fn = getattr(validator_module, contract_type["validator_func"])
    errors, warnings = validate_fn(data)

    # 6. Print warnings
    if warnings:
        print(f"\n{'─' * 60}")
        print(f"  WARNINGS for '{contract_name}'")
        print(f"{'─' * 60}")
        for w in warnings:
            print(f"  ⚠  {w}")
        print(f"{'─' * 60}\n")

    # Abort on errors
    if errors:
        print(f"\n{'═' * 60}")
        print(f"  ERRORS for '{contract_name}' — generation aborted")
        print(f"{'═' * 60}")
        for e in errors:
            print(f"  ✖  {e}")
        print(f"{'═' * 60}\n")
        sys.exit(1)

    # 7. Read CSS
    css = CSS_FILE.read_text(encoding="utf-8")

    # 8. Set up Jinja2 environment
    jinja_env = Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=False,
    )
    template = jinja_env.get_template(contract_type["template"])

    # 9. Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 10. Render both passes
    passes = [
        # (review_mode, html_filename,              pdf_filename)
        (False, f"{contract_name}_preview.html", f"{contract_name}_locacao.pdf"),
        (True,  f"{contract_name}_review.html",  f"{contract_name}_review.pdf"),
    ]

    for review_mode, html_filename, pdf_filename in passes:

        context     = build_context(data, css, review_mode)
        html_string = render_html(template, context)

        # Write HTML
        html_path = OUTPUT_DIR / html_filename
        html_path.write_text(html_string, encoding="utf-8")
        print(f"  ✔  {html_path.relative_to(ROOT)}")

        # Write PDF
        pdf_path = OUTPUT_DIR / pdf_filename
        write_pdf(html_string, pdf_path)
        print(f"  ✔  {pdf_path.relative_to(ROOT)}")

    print(f"\n  Done — 4 files written to output/\n")


if __name__ == "__main__":
    main()
