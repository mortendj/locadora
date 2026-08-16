# demo/contracts/rental/brazil/housing/short_term/full_202608.py
# DEMO DATA — fictional example of a seasonal (temporada) booking covering
# the whole house, for use as public-safe example/seed data.

from demo.people.rosangela_duarte        import data as _landlord
from demo.people.exemplo_hospede_pf import data as _tenant
from demo.properties.chacara             import data as _property

data = {
    "contract_type": "seasonal",
    "landlord": _landlord,
    "tenant":   _tenant,
    "property": _property,
    "stay": {
        "check_in_date":   "14/08/2026",
        "check_in_time":   "14:00",
        "check_out_date":  "16/08/2026",
        "check_out_time":  "11:00",
        "max_guests":      10,
        # Configuration 1 — the whole house, all bedrooms.
        "configuration": "full",
    },
    "pricing": {
        "total_amount":            "1.500,00",
        "total_amount_spelled_out": "mil e quinhentos reais",
        "number_of_nights":        2,
        "nightly_rate":            "750,00",
        "down_payment_amount":     "500,00",
        "balance_amount":          "1.000,00",
        "balance_due_date":        "13/08/2026",
        "cleaning_fee":            "150,00",
        "utilities_included":     True,
        "extra_guest_fee_per_day": "50,00",
    },
    "security_deposit": {
        "amount": "500,00",
    },
    "rules": {
        "allow_pets": True,
    },
    "termination": {
        "notice_days": 30,
    },
    "contract": {
        "date": "10 de agosto de 2026",
    },
    "witnesses": [
        {"name": "Testemunha Exemplo Um", "cpf": "000.000.000-00"},
        {"name": "Testemunha Exemplo Dois", "cpf": "000.000.000-00"},
    ],
}
