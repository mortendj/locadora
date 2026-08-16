# demo/contracts/rental/brazil/real_estate/commercial/eduardo_vestuario.py
# DEMO DATA — fictional commercial contract, structurally modeled on a
# real one, for use as public-safe example/seed data. Not a real person.
#
# See eduardo_barbearia.py in this same directory for why this moved
# here from residential/long_term and what it demonstrates.

from demo.people.rosangela_duarte    import data as _landlord
from demo.people.eduardo_prado       import data as _tenant
from demo.people.carla_prado         import data as _guarantor
from demo.properties.tucanos_175_dir import data as _property

data = {
    "contract_type": "commercial",
    "landlord":  _landlord,
    "tenant":    _tenant,
    "guarantor": _guarantor,
    "property":  _property,
    "dates": {
        "start_date":              "01/08/2026",
        "term_months":             30,
        "term_months_spelled_out": "trinta",
    },
    "security_deposit": {
        "amount": None,
    },
    "termination": {
        "penalty_months":             0,
        "penalty_months_spelled_out": "zero",
    },
    "pricing": {
        "rent":    "850,00",
        "due_day": 10,
    },
    "charges": {
        "property_tax_payer": "tenant",
    },
    "renovation":                 None,
    "registration":               None,
    "professional_registration":  None,
    "sharing":                    None,
    "contract": {
        "date": "10 de agosto de 2026",
    },
}
