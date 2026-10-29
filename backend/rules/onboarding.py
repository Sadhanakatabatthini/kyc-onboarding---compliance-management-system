from typing import Dict, Any, List, Tuple

VALID_TRANSITIONS = {
    "PENDING_EVIDENCE": ["PENDING_VERIFICATION", "EXCEPTION"],
    "PENDING_VERIFICATION": ["UNDER_REVIEW", "PENDING_EVIDENCE", "EXCEPTION"],
    "UNDER_REVIEW": ["APPROVED", "REJECTED", "PENDING_EVIDENCE", "EXCEPTION"],
    "APPROVED": ["UNDER_REVIEW", "EXCEPTION"],
    "REJECTED": ["UNDER_REVIEW", "EXCEPTION"],
    "EXCEPTION": ["UNDER_REVIEW", "PENDING_EVIDENCE", "REJECTED"]
}

def can_transition_status(current_status: str, target_status: str) -> bool:
    return target_status in VALID_TRANSITIONS.get(current_status, [])

def evaluate_onboarding_approval(
    customer: Dict[str, Any],
    completeness_percentage: float,
    missing_requirements: List[Dict[str, Any]],
    reviewer_role: str,
    beneficial_ownership_total: float = None,
    active_critical_alerts: int = 0
) -> Tuple[bool, List[str]]:
    """
    Evaluates whether a customer in UNDER_REVIEW can be transitioned to APPROVED.
    
    Approval requirements:
    1. Reviewer role must be 'Risk / Compliance Reviewer' or 'System Administrator'.
    2. Completeness percentage must be 100.0%.
    3. Zero missing mandatory requirements.
    4. For business customer (customer_type_id == 2 or code == 'BUSINESS'),
       beneficial ownership total must be > 0 and <= 100.0%.
    5. Zero active critical alerts.
    """
    reasons = []

    # 1. Role authorization
    allowed_roles = ["Risk / Compliance Reviewer", "System Administrator", "COMPLIANCE_OFFICER", "ADMIN"]
    if reviewer_role not in allowed_roles:
        reasons.append(f"Role '{reviewer_role}' is not authorized to grant KYC approvals.")

    # 2. Completeness check
    if completeness_percentage < 100.0:
        reasons.append(f"Incomplete KYC evidence: completeness is {completeness_percentage}%, expected 100.0%.")

    # 3. Missing mandatory requirements
    mandatory_missing = [r for r in missing_requirements if r.get("mandatory_flag", True)]
    if len(mandatory_missing) > 0:
        missing_codes = [r.get("requirement_code") for r in mandatory_missing]
        reasons.append(f"Missing mandatory KYC requirements: {', '.join(missing_codes)}.")

    # 4. Beneficial ownership check for business customers
    cust_type = customer.get("customer_type_id")
    if cust_type == 2:  # Business customer
        if beneficial_ownership_total is None or beneficial_ownership_total <= 0:
            reasons.append("Beneficial ownership structure is required for corporate entities.")
        elif beneficial_ownership_total > 100.00:
            reasons.append(f"Beneficial ownership total exceeds 100% ({beneficial_ownership_total}%).")

    # 5. Critical alerts
    if active_critical_alerts > 0:
        reasons.append(f"Customer has {active_critical_alerts} unresolved critical compliance alerts.")

    is_eligible = len(reasons) == 0
    return is_eligible, reasons
