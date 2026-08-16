# templates/rental/brazil/real_estate/commercial/locacao_comercial_validators.py


def _parse_brl(s):
    """Convert Brazilian currency string to float. e.g. '1.900,00' → 1900.0"""
    return float(s.replace(".", "").replace(",", "."))


def validate_locacao_comercial(data):
    """
    Validates a locacao_comercial contract dict before rendering.
    Returns (errors, warnings).
    Errors block generation. Warnings are printed but allow generation.

    This contract type is generic (any non-residential lease, with or
    without a renovation-reimbursement deal, a professional-registration
    requirement, or a space-sharing carve-out) — so only the fields
    needed for the document to be legally coherent at all (tenant
    identity, term, rent) are errors. Everything else still pending is a
    warning, not a blocker.
    """
    errors   = []
    warnings = []

    landlord     = data.get("landlord") or {}
    tenant       = data.get("tenant", {})
    prop         = data.get("property", {})
    dates        = data.get("dates", {})
    pricing      = data.get("pricing", {})
    renovation   = data.get("renovation") or {}
    registration = data.get("registration") or {}
    sharing      = data.get("sharing") or {}

    # ── Tenant required fields ───────────────────────────────────────────────
    if not tenant.get("name"):
        errors.append("ERROR: TENANT name not provided.")
    if not tenant.get("cpf") and not tenant.get("cnpj"):
        errors.append("ERROR: TENANT CPF/CNPJ not provided.")

    # ── Landlord — known to be pending in some drafts, warn only ────────────
    if not landlord.get("name"):
        warnings.append("WARNING: landlord identity not provided — intro paragraph will be left pending.")
    if not landlord.get("cpf") and not landlord.get("cnpj"):
        warnings.append("WARNING: landlord.cpf/cnpj not provided.")

    # ── Property ──────────────────────────────────────────────────────────────
    for field in ["city", "state"]:
        if not prop.get(field):
            errors.append(f"ERROR: property.{field} not provided.")
    for field in ["street_address", "neighborhood", "zip_code"]:
        if not prop.get(field):
            warnings.append(f"WARNING: property.{field} not provided.")
    if not prop.get("commercial_use_description"):
        warnings.append(
            "WARNING: property.commercial_use_description not provided — "
            "Clause 1 (objeto) and Clause 12 (destinação) will render a "
            "generic 'atividade comercial' description instead of the "
            "tenant's actual business."
        )
    if not registration.get("number"):
        warnings.append(
            "NOTE: registration.number not provided — Clause 11 will render "
            "without the averbação-at-Cartório-de-Registro-de-Imóveis "
            "obligation. This is treated as a real possibility, not a data "
            "gap: some properties (e.g. a room inside the landlord's own "
            "unregistered house) may have no matrícula at all. If this "
            "property does have one, set registration.number/registry_office."
        )

    # ── Term ──────────────────────────────────────────────────────────────────
    if not dates.get("start_date"):
        errors.append("ERROR: dates.start_date not provided.")
    if not dates.get("term_months"):
        errors.append("ERROR: dates.term_months not provided.")
    elif dates["term_months"] >= 60:
        warnings.append(
            f"NOTE: dates.term_months = {dates['term_months']} — at 60 months "
            "(5 years) or more, the tenant's ação renovatória right under Lei "
            "8.245/91 arts. 51-57 may become available (also requires 3+ years "
            "running the same business at this address), referenced in Clause 2."
        )

    # ── Rent / late payment ───────────────────────────────────────────────────
    if not pricing.get("rent"):
        errors.append("ERROR: pricing.rent not provided.")
    if not pricing.get("due_day"):
        warnings.append("WARNING: pricing.due_day not provided.")

    late_fee = pricing.get("late_payment_penalty_percent")
    if late_fee is not None and not (0 < late_fee <= 100):
        errors.append(
            f"ERROR: pricing.late_payment_penalty_percent ({late_fee}) must be "
            "between 0 and 100."
        )

    # ── Reform reimbursement (optional module) ───────────────────────────────
    if renovation.get("total_cost") and not pricing.get("initial_discount_amount"):
        warnings.append(
            "WARNING: renovation.total_cost is set but pricing.initial_discount_amount "
            "is not — the estimated abatement period (Clause 4 §3) cannot be computed."
        )

    rent_str     = pricing.get("rent")
    discount_str = pricing.get("initial_discount_amount")
    if rent_str and discount_str:
        rent = _parse_brl(rent_str)
        discount = _parse_brl(discount_str)
        if discount <= 0 or discount >= rent:
            errors.append(
                f"ERROR: pricing.initial_discount_amount (R$ {discount_str}) must be "
                f"greater than 0 and less than pricing.rent (R$ {rent_str})."
            )

    # ── Space-sharing carve-out (optional module) ────────────────────────────
    if sharing.get("allowed") and not sharing.get("description"):
        warnings.append(
            "WARNING: sharing.allowed is set but sharing.description is not — "
            "Clause 13's carve-out will render without a description of what "
            "sharing is actually permitted."
        )

    return errors, warnings
