# demo/contracts/rental/brazil/real_estate/commercial/fernanda_fisioterapia.py
# DEMO DATA — wholly fictional contract (not modeled on any real one),
# for use as public-safe example/seed data. Exercises every opt-in
# module of the commercial template that eduardo_barbearia.py/
# eduardo_vestuario.py in this same directory don't: the renovation
# reimbursement/rent-abatement deal, a filled-in professional
# registration, the space-sharing carve-out, the declining
# early-termination penalty formula, a custom late-payment fee, a cash
# security deposit (caução) instead of a fiador, and landlord-paid IPTU.

from demo.people.marisa_lima       import data as _landlord
from demo.people.fernanda_salgado  import data as _tenant
from demo.properties.margaridas_45 import data as _property

data = {
    "contract_type": "commercial",
    "landlord":  _landlord,
    "tenant":    _tenant,
    "guarantor": None,
    "property":  _property,
    "dates": {
        "start_date":              "01/03/2026",
        "term_months":             60,
        "term_months_spelled_out": "sessenta",
    },
    "security_deposit": {
        "amount": "2.500,00",
    },
    "termination": {
        "penalty_formula": "declining",
    },
    "pricing": {
        "rent":                          "1.250,00",
        "due_day":                       5,
        "initial_discount_amount":       "300,00",
        "late_payment_penalty_percent":  5,
    },
    "charges": {
        "property_tax_payer": "landlord",
    },
    "registration": None,  # still pending, matching the realistic "not averbado yet" scenario
    "renovation": {
        "description":            "reforma das instalações elétricas e hidráulicas, além de adequação acústica das salas de atendimento",
        "total_cost":              "6.000,00",
        "total_cost_spelled_out":  "seis mil reais",
    },
    "professional_registration": {
        "label":  "CREFITO",
        "number": "98765",
    },
    "sharing": {
        "allowed":     True,
        "description": "o compartilhamento das salas de atendimento com outros profissionais da área de saúde, mediante rateio de custos, para atendimento de seus próprios pacientes",
    },
    "contract": {
        "date": "1 de março de 2026",
    },
}
