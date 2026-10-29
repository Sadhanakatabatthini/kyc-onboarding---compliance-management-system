from datetime import date
from typing import List, Dict, Any, Tuple

class ConfigurationException(Exception):
    pass

def calculate_kyc_completeness(
    customer_dict: Dict[str, Any],
    requirements: List[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    verifications: List[Dict[str, Any]],
    as_of_date: date = None
) -> Tuple[float, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Calculates KYC completeness percentage and identifies satisfied vs missing requirements.
    
    Returns:
        (completeness_percentage, satisfied_requirements, missing_requirements)
    """
    if as_of_date is None:
        as_of_date = date.today()

    cust_type_id = customer_dict.get("customer_type_id")
    cust_risk = customer_dict.get("risk_level", "LOW")

    # Filter applicable requirements
    applicable_reqs = []
    for req in requirements:
        if not req.get("active_status", True):
            continue
        if req.get("customer_type_id") != cust_type_id:
            continue
        req_risk = req.get("applicable_risk_level", "ALL")
        if req_risk != "ALL" and req_risk != cust_risk:
            continue
        # Effective date range check
        eff_from = req.get("effective_from")
        eff_to = req.get("effective_to")
        if eff_from and isinstance(eff_from, str):
            eff_from = date.fromisoformat(eff_from)
        if eff_to and isinstance(eff_to, str):
            eff_to = date.fromisoformat(eff_to)

        if eff_from and as_of_date < eff_from:
            continue
        if eff_to and as_of_date > eff_to:
            continue

        applicable_reqs.append(req)

    # Edge case: zero applicable requirements is a compliance configuration error
    if len(applicable_reqs) == 0:
        raise ConfigurationException(f"No KYC requirements configured for customer type {cust_type_id} and risk level {cust_risk}")

    # Map verified documents
    # A document is satisfied if:
    # 1. document_type matches
    # 2. document_status == 'VALID'
    # 3. expiry_date is None or expiry_date >= as_of_date
    # 4. At least one verification attempt has verification_status == 'PASSED'
    passed_doc_ids = set()
    for v in verifications:
        if v.get("verification_status") == "PASSED":
            passed_doc_ids.add(v.get("document_id"))

    valid_docs_by_type = {}
    for d in documents:
        doc_type = d.get("document_type")
        doc_status = d.get("document_status")
        doc_id = d.get("document_id")
        exp = d.get("expiry_date")
        if exp and isinstance(exp, str):
            exp = date.fromisoformat(exp)

        # Check unexpired
        is_unexpired = (exp is None) or (exp >= as_of_date)
        is_passed = doc_id in passed_doc_ids or doc_status == "VALID"

        if doc_status == "VALID" and is_unexpired and is_passed:
            if doc_type not in valid_docs_by_type:
                valid_docs_by_type[doc_type] = []
            valid_docs_by_type[doc_type].append(d)

    satisfied = []
    missing = []

    for req in applicable_reqs:
        req_doc_type = req.get("document_type")
        if req_doc_type in valid_docs_by_type and len(valid_docs_by_type[req_doc_type]) > 0:
            satisfied.append({
                "requirement": req,
                "document": valid_docs_by_type[req_doc_type][0]
            })
        else:
            missing.append(req)

    completeness_percentage = round((len(satisfied) / len(applicable_reqs)) * 100.0, 2)
    return completeness_percentage, satisfied, missing
