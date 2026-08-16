# demo/contracts/rental/brazil/housing/short_term/dayuse_202610.py
# DEMO DATA — fictional example of a day-use-only seasonal (temporada)
# booking (no overnight, no bedrooms), for use as public-safe example/seed data.

from demo.people.rosangela_duarte        import data as _landlord
from demo.people.exemplo_hospede_pf import data as _tenant
from demo.properties.chacara             import data as _property

data = {
    "contract_type": "seasonal",
    "landlord": _landlord,
    "tenant":   _tenant,
    "property": _property,
    "stay": {
        "check_in_date":   "20/09/2026",
        "check_in_time":   "10:00",
        "check_out_date":  "20/09/2026",
        "check_out_time":  "22:00",
        "max_guests":      15,
        # Configuration 3 — day-use only, no bedrooms included.
        "configuration": "dayuse",
    },
    "pricing": {
        "total_amount":             "800,00",
        "total_amount_spelled_out": "oitocentos reais",
        "down_payment_amount":      "300,00",
        "balance_amount":           "500,00",
        "balance_due_date":         "18/09/2026",
        "cleaning_fee":             "100,00",
        "utilities_included":       True,
    },
    "termination": {
        "notice_days": 15,
    },
    "contract": {
        "date": "10 de agosto de 2026",
    },
}
