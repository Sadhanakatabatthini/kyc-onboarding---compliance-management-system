from flask import Blueprint, request, jsonify
from datetime import date, datetime
import json
import os
from backend.rules.anomaly_detector import detect_anomalies

exceptions_bp = Blueprint("exceptions", __name__)

DATA_DIR = "data/generated"
AUDIT_FILE = "data/generated/audit_events.json"

def _load(name):
    p = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.exists(p):
        return []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _save(name, data):
    p = os.path.join(DATA_DIR, f"{name}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@exceptions_bp.route("", methods=["GET"])
def list_exceptions():
    customers = _load("customers")
    documents = _load("documents")
    requirements = _load("kyc_requirements")
    verifications = _load("verifications")
    review_cases = _load("review_cases")
    beneficial_ownership = _load("beneficial_ownership")

    detected = detect_anomalies(
        customers=customers,
        documents=documents,
        requirements=requirements,
        verifications=verifications,
        review_cases=review_cases,
        beneficial_ownerships=beneficial_ownership,
        evaluation_date=date.today()
    )

    # Optional query filter by type or severity
    atype = request.args.get("anomaly_type")
    sev = request.args.get("severity")

    filtered = detected
    if atype:
        filtered = [x for x in filtered if x["anomaly_type"] == atype]
    if sev:
        filtered = [x for x in filtered if x["severity"] == sev]

    return jsonify({"items": filtered, "total": len(filtered)})

@exceptions_bp.route("/remediate", methods=["POST"])
def remediate_exception():
    data = request.get_json() or {}
    anomaly_type = data.get("anomaly_type")
    entity_id = data.get("entity_id")
    actor_id = request.headers.get("X-Actor-Id", "compliance_officer_01")
    remediation_notes = data.get("notes", "Corrective remediation applied per compliance policy")

    customers = _load("customers")
    documents = _load("documents")
    review_cases = _load("review_cases")
    beneficial_ownership = _load("beneficial_ownership")

    remediated = False
    affected_entity_type = "UNKNOWN"

    if anomaly_type == "EXPIRED_DOCUMENT_MARKED_VALID":
        affected_entity_type = "DOCUMENT"
        for d in documents:
            if d["document_id"] == entity_id:
                d["document_status"] = "EXPIRED"
                remediated = True
                break
        if remediated:
            _save("documents", documents)

    elif anomaly_type == "APPROVED_MISSING_MANDATORY_EVIDENCE":
        affected_entity_type = "CUSTOMER"
        for c in customers:
            if c["customer_id"] == entity_id:
                c["lifecycle_status"] = "PENDING_EVIDENCE"
                remediated = True
                break
        if remediated:
            _save("customers", customers)

    elif anomaly_type == "OWNERSHIP_PERCENTAGE_EXCEEDS_100":
        affected_entity_type = "BENEFICIAL_OWNERSHIP"
        biz_ubos = [b for b in beneficial_ownership if b["business_customer_id"] == entity_id]
        if biz_ubos:
            # Rebalance to 100%
            equal_share = round(100.0 / len(biz_ubos), 2)
            for b in biz_ubos:
                b["ownership_percentage"] = equal_share
            remediated = True
            _save("beneficial_ownership", beneficial_ownership)

    elif anomaly_type == "REVIEW_CLOSED_WITHOUT_RESOLUTION":
        affected_entity_type = "REVIEW_CASE"
        for r in review_cases:
            if r["review_id"] == entity_id:
                r["resolution_code"] = "EXCEPTION_GRANTED"
                r["resolution_notes"] = remediation_notes
                remediated = True
                break
        if remediated:
            _save("review_cases", review_cases)

    elif anomaly_type == "DUPLICATE_DOCUMENT_REFERENCE":
        affected_entity_type = "DOCUMENT"
        matching_docs = [d for d in documents if d.get("document_reference") == entity_id]
        if len(matching_docs) > 1:
            # Append suffix to differentiate
            matching_docs[1]["document_reference"] = f"{entity_id}-AMEND"
            remediated = True
            _save("documents", documents)

    if remediated:
        # Audit log
        audits = _load("audit_events")
        audits.append({
            "audit_event_id": len(audits) + 1,
            "entity_type": affected_entity_type,
            "entity_id": str(entity_id),
            "event_type": "ANOMALY_RESOLVED",
            "actor_id": actor_id,
            "event_timestamp": datetime.utcnow().isoformat(),
            "previous_values": {"anomaly_detected": anomaly_type},
            "new_values": {"remediated": True},
            "reason": remediation_notes,
            "correlation_id": f"REMED-{entity_id}"
        })
        _save("audit_events", audits)
        return jsonify({"success": True, "message": f"Remediated {anomaly_type} for entity {entity_id}"})

    return jsonify({"error": "Entity or anomaly pattern not found for remediation"}), 404
