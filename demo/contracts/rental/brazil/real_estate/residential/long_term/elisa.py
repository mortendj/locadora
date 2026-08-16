# demo/contracts/rental/brazil/housing/long_term/elisa.py
# DEMO DATA — fictional residential contract, structurally modeled on a
# real one, for use as public-safe example/seed data. Not a real person.

from demo.people.elisa_esteves      import data as _tenant
from demo.people.rosangela_duarte   import data as _landlord
from demo.properties.garcas_10      import data as _property

data = {
    "landlord":  _landlord,
    "tenant":    _tenant,
    "guarantor": None,
    "property":  _property,
    "dates": {
        "start_date":              "11/07/2026",
        "term_months":             30,
        "term_months_spelled_out": "trinta",
    },
    "security_deposit": {
        "amount": None,
    },
    "termination": {
        "penalty_months":             0,
        "penalty_months_spelled_out": None,
    },
    "pricing": {
        "rent":                    "950,00",
        "due_day":                 6,
        "early_payment_discount":  "100,00",
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
