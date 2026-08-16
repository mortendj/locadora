# demo/contracts/rental/brazil/housing/long_term/eduardo_barbearia.py
# DEMO DATA — fictional commercial contract, structurally modeled on a
# real one, for use as public-safe example/seed data. Not a real person.

from demo.people.rosangela_duarte    import data as _landlord
from demo.people.eduardo_prado       import data as _tenant
from demo.people.carla_prado         import data as _guarantor
from demo.properties.tucanos_175_esq import data as _property

data = {
    "landlord":  _landlord,
    "tenant":    _tenant,
    "guarantor": _guarantor,
    "property":  _property,
    "dates": {
        "start_date":              "10/08/2026",
        "term_months":             30,
        "term_months_spelled_out": "trinta",
    },
    "security_deposit": {
        "amount": None,
    },
    "termination": {
        "penalty_months":             0,
        "penalty_months_spelled_out": "três",
    },
    "pricing": {
        "rent":                    "850,00",
        "due_day":                 10,
        "early_payment_discount":  "150,00",
        "initial_discount_months": None,
        "initial_discount_amount": None,
    },
    "charges": {
        "property_tax_payer": "tenant",
    },
    "contract": {
        "date": "10 de agosto de 2026",
    },
}
