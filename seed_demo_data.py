# seed_demo_data.py
#
# Seeds contracter_demo.db from the anonymized demo dataset (see
# demo/). Not one-off — the demo .py files are the permanent
# source of truth for demo data, and contracter_demo.db is a gitignored
# derived artifact, so this is the only way to (re)create it, including
# after a fresh clone. Always targets the demo database regardless of
# CONTRACTER_DB — see db.use_database() below.

import db

from demo.people.rosangela_duarte  import data as landlord_data
from demo.people.elisa_esteves     import data as elisa_data
from demo.people.carla_prado       import data as carla_data
from demo.people.eduardo_prado     import data as eduardo_data
from demo.people.guilherme_marques import data as guilherme_data
from demo.people.marisa_lima       import data as marisa_data
from demo.people.fernanda_salgado  import data as fernanda_data

from demo.properties.garcas_10         import data as garcas_data
from demo.properties.tucanos_175_apto2 import data as apto2_data
from demo.properties.tucanos_175_dir   import data as dir_data
from demo.properties.tucanos_175_esq   import data as esq_data
from demo.properties.chacara           import data as chacara_data
from demo.properties.margaridas_45     import data as margaridas_data

from demo.contracts.rental.brazil.real_estate.residential.long_term.elisa      import data as elisa_contract
from demo.contracts.rental.brazil.real_estate.residential.long_term.guilherme  import data as guilherme_contract

from demo.contracts.rental.brazil.real_estate.residential.short_term.full_202608     import data as full_contract
from demo.contracts.rental.brazil.real_estate.residential.short_term.no_suite_202609 import data as no_suite_contract
from demo.contracts.rental.brazil.real_estate.residential.short_term.dayuse_202610   import data as dayuse_contract

from demo.contracts.rental.brazil.real_estate.commercial.eduardo_barbearia    import data as barbearia_contract
from demo.contracts.rental.brazil.real_estate.commercial.eduardo_vestuario    import data as vestuario_contract
from demo.contracts.rental.brazil.real_estate.commercial.fernanda_fisioterapia import data as fernanda_contract


def _insert_residential(contract_data, landlord_id, tenant_id, guarantor_id, property_id):
    details = {
        **contract_data["dates"],
        "security_deposit_amount": contract_data["security_deposit"]["amount"],
        **contract_data["termination"],
        **contract_data["pricing"],
        "property_tax_payer": contract_data["charges"]["property_tax_payer"],
    }
    return db.insert_contract(
        contract_type="residential",
        landlord_id=landlord_id,
        tenant_id=tenant_id,
        guarantor_id=guarantor_id,
        property_id=property_id,
        contract_date=contract_data["contract"]["date"],
        details=details,
    )


def _insert_commercial(contract_data, landlord_id, tenant_id, guarantor_id, property_id):
    renovation                 = contract_data.get("renovation") or {}
    registration                = contract_data.get("registration") or {}
    professional_registration   = contract_data.get("professional_registration") or {}
    sharing                      = contract_data.get("sharing") or {}
    termination                  = contract_data.get("termination") or {}
    details = {
        **contract_data["dates"],
        **contract_data["pricing"],
        "security_deposit_amount":   (contract_data.get("security_deposit") or {}).get("amount"),
        "penalty_months":            termination.get("penalty_months"),
        "penalty_months_spelled_out": termination.get("penalty_months_spelled_out"),
        "property_tax_payer":        contract_data["charges"]["property_tax_payer"],
        "extra": {
            "renovation_description":            renovation.get("description"),
            "renovation_total_cost":              renovation.get("total_cost"),
            "renovation_total_cost_spelled_out":  renovation.get("total_cost_spelled_out"),
            "registration_number":                registration.get("number"),
            "registry_office":                    registration.get("registry_office"),
            "professional_registration_label":    professional_registration.get("label"),
            "professional_registration_number":   professional_registration.get("number"),
            "penalty_formula":                    termination.get("penalty_formula"),
            "sharing_allowed":                    sharing.get("allowed"),
            "sharing_description":                sharing.get("description"),
        },
    }
    return db.insert_contract(
        contract_type="commercial",
        landlord_id=landlord_id,
        tenant_id=tenant_id,
        guarantor_id=guarantor_id,
        property_id=property_id,
        contract_date=contract_data["contract"]["date"],
        details=details,
    )


def _insert_short_term(contract_data, landlord_id, property_id):
    # Temporada guests are per-booking by design — each booking's tenant
    # is its own person row, not shared/reused like the landlord/property.
    tenant_id = db.insert_person(contract_data["tenant"])
    details = {
        **contract_data["stay"],
        **contract_data["pricing"],
        "security_deposit_amount": (contract_data.get("security_deposit") or {}).get("amount"),
        **(contract_data.get("rules") or {}),
        **contract_data["termination"],
    }
    return db.insert_contract(
        contract_type="short_term",
        landlord_id=landlord_id,
        tenant_id=tenant_id,
        property_id=property_id,
        contract_date=contract_data["contract"]["date"],
        details=details,
        witnesses=contract_data.get("witnesses"),
    )


def main():
    # Always the demo database, regardless of CONTRACTER_DB — this script
    # must never be able to reseed the real one.
    db.use_database(db.DEMO_DB_PATH)
    db.init_db()

    # People — inserted once, reused across every contract that names them.
    landlord_id  = db.insert_person(landlord_data)
    elisa_id     = db.insert_person(elisa_data)
    carla_id     = db.insert_person(carla_data)
    eduardo_id   = db.insert_person(eduardo_data)
    guilherme_id = db.insert_person(guilherme_data)
    marisa_id    = db.insert_person(marisa_data)
    fernanda_id  = db.insert_person(fernanda_data)

    # Properties — inserted once, reused across every contract on them.
    garcas_id     = db.insert_property(garcas_data)
    apto2_id      = db.insert_property(apto2_data)
    dir_id        = db.insert_property(dir_data)
    esq_id        = db.insert_property(esq_data)
    chacara_id    = db.insert_property(chacara_data)
    margaridas_id = db.insert_property(margaridas_data)

    residential_ids = [
        _insert_residential(elisa_contract,      landlord_id, elisa_id,     None,       garcas_id),
        _insert_residential(guilherme_contract,  landlord_id, guilherme_id, eduardo_id, apto2_id),
    ]

    commercial_ids = [
        _insert_commercial(barbearia_contract,  landlord_id, eduardo_id,   carla_id, esq_id),
        _insert_commercial(vestuario_contract,  landlord_id, eduardo_id,   carla_id, dir_id),
        _insert_commercial(fernanda_contract,   marisa_id,   fernanda_id,  None,     margaridas_id),
    ]

    short_term_ids = [
        _insert_short_term(full_contract,     landlord_id, chacara_id),
        _insert_short_term(no_suite_contract,  landlord_id, chacara_id),
        _insert_short_term(dayuse_contract,    landlord_id, chacara_id),
    ]

    print(f"Inserted {len(residential_ids)} residential + {len(commercial_ids)} commercial + "
          f"{len(short_term_ids)} short_term contracts "
          f"(IDs: {residential_ids + commercial_ids + short_term_ids}).")
    print(f"Database: {db.DB_PATH}")


if __name__ == "__main__":
    main()
