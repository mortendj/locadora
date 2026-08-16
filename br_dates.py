# br_dates.py — shared Brazilian date parsing/formatting helpers.
# Extracted from main.py so validators can reuse them without importing main.

from datetime import date


def parse_br_date(date_str: str) -> date:
    """Parse DD/MM/YYYY → datetime.date."""
    day, month, year = date_str.strip().split("/")
    return date(int(year), int(month), int(day))


def format_br_date(d: date) -> str:
    """Format datetime.date → DD/MM/YYYY."""
    return d.strftime("%d/%m/%Y")
