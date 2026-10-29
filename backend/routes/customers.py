from flask import Blueprint, request, jsonify
from datetime import date, datetime
import json
import os
from backend.rules.completeness import calculate_kyc_completeness
from backend.rules.onboarding import evaluate_onboarding_approval, can_transition_status

customers_bp = Blueprint("customers", __name__)

DATA_FILE = "data/generated/customers.json"
DOCS_FILE = "data/generated/documents.json"
REQS_FILE = "data/generated/kyc_requirements.json"
VER_FILE = "data/generated/verifications.json"
AUDIT_FILE = "data/generated/audit_events.json"
UBO_FILE = "data/generated/beneficial_ownership.json"

def _load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@customers_bp.route("", methods=["GET"])
def list_customers():
    customers = _load_json(DATA_FILE)
    
    # Query parameters: search, status, type, risk, limit, offset
    search = request.args.get("search", "").lower()
    status = request.args.get("status")
    ctype = request.args.get("customer_type_id")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))

    filtered = customers
    if search:
        filtered = [c for c in filtered if search in c["customer_id"].lower() or search in c["legal_name"].lower()]
    if status:
        filtered = [c for c in filtered if c["lifecycle_status"] == status]
    if ctype:
        filtered = [c for c in filtered if str(c["customer_type_id"]) == str(ctype)]

    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start:start + page_size]

    return jsonify({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
    })

@customers_bp.route("/<customer_id>", methods=["GET"])
def get_customer(customer_id):
    customers = _load_json(DATA_FILE)
    cust = next((c for c in customers if c["customer_id"] == customer_id), None)
    if not cust:
        return jsonify({"error": "Customer not found"}), 404

    docs = [d for d in _load_json(DOCS_FILE) if d["customer_id"] == customer_id]
    reqs = _load_json(REQS_FILE)
    vers = _load_json(VER_FILE)
    ubos = [u for u in _load_json(UBO_FILE) if u.get("business_customer_id") == customer_id]

    pct, sat, miss = calculate_kyc_completeness(cust, reqs, docs, vers, date.today())

    return jsonify({
        "customer": cust,
        "completeness_percentage": pct,
        "satisfied_requirements": sat,
        "missing_requirements": miss,
        "documents": docs,
        "beneficial_ownership": ubos
    })

@customers_bp.route("", methods=["POST"])
def create_customer():
    data = request.get_json() or {}
    legal_name = data.get("legal_name")
    ctype_id = data.get("customer_type_id", 1)
    country_code = data.get("country_code", "US")

    if not legal_name:
        return jsonify({"error": "legal_name is required"}), 400

    customers = _load_json(DATA_FILE)
    cid = f"CUS-{len(customers) + 1:06d}"
    today_iso = date.today().isoformat()

    new_cust = {
        "customer_id": cid,
        "customer_type_id": int(ctype_id),
        "legal_name": legal_name,
        "country_code": country_code,
        "onboarding_date": today_iso,
        "lifecycle_status": "PENDING_EVIDENCE",
        "onboarding_channel": data.get("onboarding_channel", "DIGITAL_PORTAL"),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    customers.append(new_cust)
    _save_json(DATA_FILE, customers)

    # Record Audit Event
    audits = _load_json(AUDIT_FILE)
    audits.append({
        "audit_event_id": len(audits) + 1,
        "entity_type": "CUSTOMER",
        "entity_id": cid,
        "event_type": "CUSTOMER_CREATED",
        "actor_id": request.headers.get("X-Actor-Id", "operations_analyst_01"),
        "event_timestamp": datetime.utcnow().isoformat(),
        "previous_values": None,
        "new_values": new_cust,
        "reason": "New onboarding customer created",
        "correlation_id": f"CORR-{cid}"
    })
    _save_json(AUDIT_FILE, audits)

    return jsonify(new_cust), 201

@customers_bp.route("/<customer_id>/decision", methods=["POST"])
def evaluate_decision(customer_id):
    customers = _load_json(DATA_FILE)
    cust = next((c for c in customers if c["customer_id"] == customer_id), None)
    if not cust:
        return jsonify({"error": "Customer not found"}), 404

    data = request.get_json() or {}
    target_status = data.get("target_status")
    actor_id = request.headers.get("X-Actor-Id", "risk_reviewer_01")
    actor_role = request.headers.get("X-Actor-Role", "Risk / Compliance Reviewer")
    reason = data.get("reason", "Routine decision evaluation")

    if not can_transition_status(cust["lifecycle_status"], target_status):
        return jsonify({
            "error": f"Invalid lifecycle status transition from '{cust['lifecycle_status']}' to '{target_status}'"
        }), 400

    docs = [d for d in _load_json(DOCS_FILE) if d["customer_id"] == customer_id]
    reqs = _load_json(REQS_FILE)
    vers = _load_json(VER_FILE)
    ubos = [u for u in _load_json(UBO_FILE) if u.get("business_customer_id") == customer_id]
    ubo_total = sum(float(u.get("ownership_percentage", 0)) for u in ubos) if ubos else None

    pct, sat, miss = calculate_kyc_completeness(cust, reqs, docs, vers, date.today())

    if target_status == "APPROVED":
        eligible, reasons = evaluate_onboarding_approval(
            customer=cust,
            completeness_percentage=pct,
            missing_requirements=miss,
            reviewer_role=actor_role,
            beneficial_ownership_total=ubo_total
        )
        if not eligible:
            return jsonify({
                "error": "Customer cannot be approved",
                "reasons": reasons
            }), 422

    # Apply transition
    prev_status = cust["lifecycle_status"]
    cust["lifecycle_status"] = target_status
    cust["updated_at"] = datetime.utcnow().isoformat()
    _save_json(DATA_FILE, customers)

    # Audit log
    audits = _load_json(AUDIT_FILE)
    audits.append({
        "audit_event_id": len(audits) + 1,
        "entity_type": "CUSTOMER",
        "entity_id": customer_id,
        "event_type": "STATUS_TRANSITION",
        "actor_id": actor_id,
        "event_timestamp": datetime.utcnow().isoformat(),
        "previous_values": {"lifecycle_status": prev_status},
        "new_values": {"lifecycle_status": target_status},
        "reason": reason,
        "correlation_id": f"CORR-{customer_id}"
    })
    _save_json(AUDIT_FILE, audits)

    return jsonify({"success": True, "customer": cust, "previous_status": prev_status})
