from datetime import date
from typing import List, Dict, Any

def detect_anomalies(
    customers: List[Dict[str, Any]],
    documents: List[Dict[str, Any]],
    requirements: List[Dict[str, Any]],
    verifications: List[Dict[str, Any]],
    review_cases: List[Dict[str, Any]],
    beneficial_ownerships: List[Dict[str, Any]],
    evaluation_date: date = None
) -> List[Dict[str, Any]]:
    """
    Independent anomaly detection engine that evaluates operational database records
    WITHOUT access to ground-truth labels.
    
    Detects:
    1. ANOMALY-001: Expired document marked valid.
    2. ANOMALY-002: Customer approved despite missing mandatory evidence.
    3. ANOMALY-003: Beneficial ownership percentage exceeding 100%.
    4. ANOMALY-004: Review case closed without valid resolution details.
    5. ANOMALY-005: Duplicate document reference shared by unrelated customers.
    """
    if evaluation_date is None:
        evaluation_date = date.today()

    detected = []

    # Map helpers
    doc_map = {d["document_id"]: d for d in documents}
    verifications_by_doc = {}
    for v in verifications:
        doc_id = v.get("document_id")
        verifications_by_doc.setdefault(doc_id, []).append(v)

    # 1. Anomaly 1: Expired document marked valid
    for doc in documents:
        exp = doc.get("expiry_date")
        if exp:
            if isinstance(exp, str):
                exp = date.fromisoformat(exp)
            if exp < evaluation_date and doc.get("document_status") == "VALID":
                detected.append({
                    "anomaly_type": "EXPIRED_DOCUMENT_MARKED_VALID",
                    "affected_entity_type": "DOCUMENT",
                    "affected_entity_id": doc.get("document_id"),
                    "customer_id": doc.get("customer_id"),
                    "severity": "CRITICAL",
                    "description": f"Document {doc.get('document_id')} expired on {exp.isoformat()} but status is recorded as VALID.",
                    "expected_action": "Update document_status to 'EXPIRED' and trigger customer compliance review.",
                    "detected_at": evaluation_date.isoformat()
                })

    # 2. Anomaly 2: Customer approved despite missing mandatory evidence
    # Group documents by customer
    docs_by_customer = {}
    for doc in documents:
        docs_by_customer.setdefault(doc.get("customer_id"), []).append(doc)

    for cust in customers:
        if cust.get("lifecycle_status") == "APPROVED":
            cust_id = cust.get("customer_id")
            cust_type_id = cust.get("customer_type_id")
            cust_docs = docs_by_customer.get(cust_id, [])

            # Check mandatory requirements
            cust_reqs = [
                r for r in requirements
                if r.get("customer_type_id") == cust_type_id and r.get("mandatory_flag", True)
            ]

            valid_types = set()
            for d in cust_docs:
                exp = d.get("expiry_date")
                if exp and isinstance(exp, str):
                    exp = date.fromisoformat(exp)
                is_unexpired = (exp is None) or (exp >= evaluation_date)
                if d.get("document_status") == "VALID" and is_unexpired:
                    valid_types.add(d.get("document_type"))

            missing_reqs = [r for r in cust_reqs if r.get("document_type") not in valid_types]
            if len(missing_reqs) > 0:
                missing_names = [r.get("requirement_code") for r in missing_reqs]
                detected.append({
                    "anomaly_type": "APPROVED_MISSING_MANDATORY_EVIDENCE",
                    "affected_entity_type": "CUSTOMER",
                    "affected_entity_id": cust_id,
                    "customer_id": cust_id,
                    "severity": "CRITICAL",
                    "description": f"Customer {cust_id} is marked APPROVED but lacks mandatory valid evidence: {', '.join(missing_names)}.",
                    "expected_action": "Revert customer lifecycle_status to 'UNDER_REVIEW' or 'PENDING_EVIDENCE' and raise urgent alert.",
                    "detected_at": evaluation_date.isoformat()
                })

    # 3. Anomaly 3: Ownership percentage exceeding 100%
    ownership_by_biz = {}
    for ubo in beneficial_ownerships:
        biz_id = ubo.get("business_customer_id")
        pct = float(ubo.get("ownership_percentage", 0.0))
        ownership_by_biz.setdefault(biz_id, []).append((ubo.get("ownership_id"), pct))

    for biz_id, ubos in ownership_by_biz.items():
        total_pct = sum(u[1] for u in ubos)
        if round(total_pct, 2) > 100.00:
            detected.append({
                "anomaly_type": "OWNERSHIP_PERCENTAGE_EXCEEDS_100",
                "affected_entity_type": "BENEFICIAL_OWNERSHIP",
                "affected_entity_id": biz_id,
                "customer_id": biz_id,
                "severity": "HIGH",
                "description": f"Business entity {biz_id} has cumulative beneficial ownership of {round(total_pct, 2)}% (exceeds 100.00%).",
                "expected_action": "Freeze corporate approval, request cap table reconciliation and amended shareholder registry.",
                "detected_at": evaluation_date.isoformat()
            })

    # 4. Anomaly 4: Review closed without valid resolution
    for rev in review_cases:
        status = rev.get("review_status")
        if status == "COMPLETED":
            code = rev.get("resolution_code")
            notes = rev.get("resolution_notes")
            if not code or not notes or not str(notes).strip():
                detected.append({
                    "anomaly_type": "REVIEW_CLOSED_WITHOUT_RESOLUTION",
                    "affected_entity_type": "REVIEW_CASE",
                    "affected_entity_id": rev.get("review_id"),
                    "customer_id": rev.get("customer_id"),
                    "severity": "HIGH",
                    "description": f"Review {rev.get('review_id')} is marked COMPLETED but lacks required resolution code or notes.",
                    "expected_action": "Reopen review case to 'IN_PROGRESS' and enforce mandatory resolution documentation.",
                    "detected_at": evaluation_date.isoformat()
                })

    # 5. Anomaly 5: Duplicate document reference across unrelated customers
    refs_to_customers = {}
    for doc in documents:
        ref = doc.get("document_reference")
        cid = doc.get("customer_id")
        did = doc.get("document_id")
        if ref and cid:
            refs_to_customers.setdefault(ref, set()).add((cid, did))

    for ref, cust_set in refs_to_customers.items():
        distinct_customers = set(c[0] for c in cust_set)
        if len(distinct_customers) > 1:
            affected_cids = sorted(list(distinct_customers))
            detected.append({
                "anomaly_type": "DUPLICATE_DOCUMENT_REFERENCE",
                "affected_entity_type": "DOCUMENT",
                "affected_entity_id": ref,
                "customer_id": affected_cids[0],
                "severity": "MEDIUM",
                "description": f"Document reference '{ref}' is attached to multiple distinct customers: {', '.join(affected_cids)}.",
                "expected_action": "Investigate potential document fraud or operational indexing collision; re-verify identity.",
                "detected_at": evaluation_date.isoformat()
            })

    return detected
