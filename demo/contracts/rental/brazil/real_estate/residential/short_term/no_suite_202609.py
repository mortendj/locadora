# demo/contracts/rental/brazil/real_estate/residential/short_term/no_suite_202609.py
# DEMO DATA — fictional example of a seasonal (temporada) booking with the
# suite locked off (company/CNPJ tenant), for use as public-safe example/seed data.

from demo.people.rosangela_duarte        import data as _landlord
from demo.people.exemplo_hospede_pj import data as _tenant
from demo.properties.chacara             import data as _property

data = {
    "contract_type": "seasonal",
    "landlord": _landlord,
    "tenant":   _tenant,
    "property": _property,
    "stay": {
        "check_in_date":  "01/09/2026",
        "check_out_date": "05/09/2026",
        "max_guests":     20,
        # Configuration 2 — suite locked off, other two bedrooms available.
        "configuration": "no_suite",
    },
    "pricing": {
        "total_amount":            "3.200,00",
        "total_amount_spelled_out": "três mil e duzentos reais",
        "down_payment_amount":     "1.200,00",
        "balance_amount":          "2.000,00",
        "balance_due_date":        "30/08/2026",
        "utilities_included":     True,
    },
    "termination": {
        "notice_days": 30,
    },
    "contract": {
        "date": "10 de agosto de 2026",
    },
}
