# templates/contracts/rental/brazil/locacao_temporada_validators.py

from br_dates import parse_br_date

MAX_SHORT_TERM_DAYS = 90


def _parse_brl(s):
    """Convert Brazilian currency string to float. e.g. '1.900,00' → 1900.0"""
    return float(s.replace(".", "").replace(",", "."))


def validate_locacao_temporada(data):
    """
    Validates a locacao_temporada contract dict before rendering.
    Returns (errors, warnings).
    Errors block generation. Warnings are printed but allow generation.
    """
    errors   = []
    warnings = []

    tenant      = data.get("tenant", {})
    prop        = data.get("property", {})
    stay        = data.get("stay", {})
    pricing     = data.get("pricing", {})
    termination = data.get("termination", {})
    rules       = data.get("rules", {}) or {}

    # ── Tenant required fields ───────────────────────────────────────────────
    tenant_type = tenant.get("type")
    if tenant_type not in ("individual", "company"):
        errors.append(
            "ERROR: tenant.type must be 'individual' or 'company' "
            f"(received: {tenant_type!r})."
        )
    elif tenant_type == "individual":
        if not tenant.get("name"):
            errors.append("ERROR: TENANT (individual) name not provided.")
        if not tenant.get("cpf"):
            errors.append("ERROR: TENANT CPF not provided.")
    else:  # company
        if not tenant.get("company_name"):
            errors.append("ERROR: TENANT (company) company_name not provided.")
        if not tenant.get("cnpj"):
            errors.append("ERROR: TENANT CNPJ not provided.")
        representative = tenant.get("representative", {})
        if not representative.get("name"):
            errors.append("ERROR: TENANT's legal representative name not provided.")
        if not representative.get("cpf"):
            errors.append("ERROR: TENANT's legal representative CPF not provided.")

    # ── Property required fields ─────────────────────────────────────────────
    for field in ["street_address", "neighborhood", "city", "state", "zip_code"]:
        if not prop.get(field):
            errors.append(f"ERROR: property.{field} not provided.")

    # ── Stay (dates) ──────────────────────────────────────────────────────────
    check_in_str  = stay.get("check_in_date")
    check_out_str = stay.get("check_out_date")

    if not check_in_str:
        errors.append("ERROR: stay.check_in_date not provided.")
    if not check_out_str:
        errors.append("ERROR: stay.check_out_date not provided.")

    if check_in_str and check_out_str:
        check_in  = parse_br_date(check_in_str)
        check_out = parse_br_date(check_out_str)

        if check_out < check_in:
            errors.append(
                "ERROR: stay.check_out_date must not be before stay.check_in_date."
            )
        elif check_out == check_in:
            # Same-day (day-use, no overnight) booking — only valid if
            # check-in/check-out times are given and check-out is later.
            check_in_time  = stay.get("check_in_time")
            check_out_time = stay.get("check_out_time")
            if not check_in_time or not check_out_time:
                errors.append(
                    "ERROR: stay.check_in_date and stay.check_out_date are "
                    "the same day — stay.check_in_time and stay.check_out_time "
                    "are required to establish a same-day (day-use) booking."
                )
            elif check_out_time <= check_in_time:
                errors.append(
                    "ERROR: stay.check_out_time must be after stay.check_in_time "
                    "for a same-day booking."
                )
        else:
            duration_days = (check_out - check_in).days
            if duration_days > MAX_SHORT_TERM_DAYS:
                errors.append(
                    f"LEGAL ERROR: A short-term rental (locação por temporada) "
                    f"cannot exceed {MAX_SHORT_TERM_DAYS} days "
                    f"(duration provided: {duration_days} days)."
                )

    if not stay.get("max_guests"):
        warnings.append(
            "WARNING: stay.max_guests not provided. The occupancy-limit "
            "clause will have no value set."
        )

    # ── Inventory (Lei 8.245/91, art. 48, parágrafo único) ────────────────────
    if not prop.get("common_areas") and not prop.get("bedrooms"):
        warnings.append(
            "WARNING: property.common_areas / property.bedrooms not provided. "
            "Lei 8.245/91 (art. 48, parágrafo único) expects a short-term-rental "
            "contract to list the furniture/items provided with the property; "
            "the corresponding clause will be omitted."
        )

    # ── Bedroom configuration ─────────────────────────────────────────────────
    known_configurations = prop.get("configurations") or {}
    configuration = stay.get("configuration")
    if configuration is None:
        warnings.append(
            "WARNING: stay.configuration was not declared. The contract "
            "will assume a day-use booking with no overnight stay (no bedrooms "
            "included)."
        )
    elif configuration not in known_configurations:
        errors.append(
            f"ERROR: stay.configuration references '{configuration}', which "
            f"is not a key in property.configurations."
        )

    # ── Pets ──────────────────────────────────────────────────────────────────
    if rules.get("allow_pets") not in (True, False):
        warnings.append(
            "WARNING: rules.allow_pets was not explicitly declared "
            "(True/False). The contract will assume pets are not allowed."
        )

    # ── Pricing required fields ──────────────────────────────────────────────
    if not pricing.get("total_amount"):
        errors.append("ERROR: pricing.total_amount not provided.")
    if not pricing.get("total_amount_spelled_out"):
        errors.append(
            "ERROR: pricing.total_amount_spelled_out not provided "
            "(e.g. 'mil e quinhentos reais')."
        )

    down_payment_str = pricing.get("down_payment_amount")
    balance_str       = pricing.get("balance_amount")
    total_str         = pricing.get("total_amount")
    if down_payment_str and balance_str and total_str:
        total_paid = _parse_brl(down_payment_str) + _parse_brl(balance_str)
        total = _parse_brl(total_str)
        if abs(total_paid - total) > 0.01:
            warnings.append(
                f"WARNING: down payment (R$ {down_payment_str}) + balance "
                f"(R$ {balance_str}) = R$ {total_paid:.2f}, which does not "
                f"match total_amount (R$ {total_str})."
            )

    number_of_nights = pricing.get("number_of_nights")
    nightly_rate      = pricing.get("nightly_rate")
    if number_of_nights and nightly_rate and total_str:
        expected = number_of_nights * _parse_brl(nightly_rate)
        total = _parse_brl(total_str)
        if abs(expected - total) > 0.01:
            warnings.append(
                f"WARNING: {number_of_nights} night(s) x R$ {nightly_rate} = "
                f"R$ {expected:.2f}, which does not match total_amount "
                f"(R$ {total_str})."
            )

    # ── Termination ───────────────────────────────────────────────────────────
    if termination.get("notice_days") is None:
        errors.append("ERROR: termination.notice_days not provided.")

    for field in ("forfeit_percent_30_days_or_more", "forfeit_percent_under_30_days"):
        pct = termination.get(field)
        if pct is not None and not (0 <= pct <= 100):
            errors.append(f"ERROR: termination.{field} must be between 0 and 100 (received: {pct}).")

    return errors, warnings
