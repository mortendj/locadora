# templates/contracts/rental/brazil/locacao_validators.py


def _parse_brl(s):
    """Convert Brazilian currency string to float. e.g. '1.900,00' → 1900.0"""
    return float(s.replace(".", "").replace(",", "."))


def validate_locacao(data):
    """
    Validates a locacao contract dict before rendering.
    Returns (errors, warnings).
    Errors block generation. Warnings are printed but allow generation.
    """
    errors   = []
    warnings = []

    guarantor        = data.get("guarantor")
    security_deposit = data.get("security_deposit", {})
    pricing          = data.get("pricing", {})
    termination      = data.get("termination", {})
    dates            = data.get("dates", {})
    prop             = data.get("property", {})
    tenant           = data.get("tenant", {})

    # ── Security deposit ─────────────────────────────────────────────────
    deposit_amount = security_deposit.get("amount")

    if guarantor is not None and deposit_amount is not None:
        errors.append(
            "LEGAL ERROR: Illegal combination of guarantees. A guarantor and "
            "a security deposit cannot both be required at the same time."
        )

    if deposit_amount is not None:
        rent_str = pricing.get("rent")
        if rent_str:
            rent_float    = _parse_brl(rent_str)
            deposit_float = _parse_brl(deposit_amount)
            if rent_float > 0 and deposit_float > rent_float * 3:
                errors.append(
                    f"ERROR: Security deposit of R$ {deposit_amount} exceeds "
                    f"the legal limit of 3 months' rent "
                    f"(R$ {rent_str} x 3)."
                )

    # ── Guarantee warnings ────────────────────────────────────────────────
    if deposit_amount is None and guarantor is None:
        warnings.append(
            "WARNING: No security deposit or guarantor defined. The contract "
            "will explicitly state that no guarantee is required."
        )

    # ── Tenant required fields ───────────────────────────────────────────
    if not tenant.get("name"):
        errors.append("ERROR: TENANT name not provided.")
    if not tenant.get("cpf"):
        errors.append("ERROR: TENANT CPF not provided.")

    if not tenant.get("rg"):
        warnings.append(
            "WARNING: TENANT RG not provided. Only the CPF will be included "
            "in the contract."
        )

    # ── Property required fields ─────────────────────────────────────────
    for field in ["street_address", "neighborhood", "city", "state", "zip_code"]:
        if not prop.get(field):
            errors.append(f"ERROR: property.{field} not provided.")

    # ── Dates required fields ────────────────────────────────────────────
    if not dates.get("start_date"):
        errors.append("ERROR: Start date not provided.")
    if not dates.get("term_months"):
        errors.append("ERROR: Term (in months) not provided.")

    if not dates.get("term_months_spelled_out"):
        errors.append(
            "ERROR: dates.term_months_spelled_out not provided "
            "(e.g. 'trinta' for 30 months)."
        )

    # ── Pricing required fields ──────────────────────────────────────────
    if not pricing.get("rent"):
        errors.append("ERROR: Rent amount not provided.")

    # ── Guarantor warnings ───────────────────────────────────────────────
    if guarantor and not guarantor.get("full_address"):
        warnings.append(
            "WARNING: GUARANTOR address not provided. The address will be "
            "omitted from the contract."
        )

    # ── Termination ───────────────────────────────────────────────────────
    penalty_months = termination.get("penalty_months", 0)

    if penalty_months < 0:
        errors.append("ERROR: termination.penalty_months cannot be negative.")

    if penalty_months > 0 and not termination.get("penalty_months_spelled_out"):
        errors.append(
            "ERROR: termination.penalty_months_spelled_out is required "
            "when penalty_months > 0."
        )

    if penalty_months > 3:
        warnings.append(
            f"WARNING: termination.penalty_months = {penalty_months} is "
            "unusual. Verify this matches what was negotiated."
        )

    return errors, warnings
