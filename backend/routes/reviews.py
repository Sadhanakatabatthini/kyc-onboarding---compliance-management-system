from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import os

reviews_bp = Blueprint("reviews", __name__)

REVIEWS_FILE = "data/generated/review_cases.json"
AUDIT_FILE = "data/generated/audit_events.json"

def _load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@reviews_bp.route("", methods=["GET"])
def list_reviews():
    reviews = _load_json(REVIEWS_FILE)
    status = request.args.get("status")
    cid = request.args.get("customer_id")
    rtype = request.args.get("review_type")

    filtered = reviews
    if status:
        filtered = [r for r in filtered if r["review_status"] == status]
    if cid:
        filtered = [r for r in filtered if r["customer_id"] == cid]
    if rtype:
        filtered = [r for r in filtered if r["review_type"] == rtype]

    return jsonify({"items": filtered, "total": len(filtered)})

@reviews_bp.route("/<review_id>/close", methods=["POST"])
def close_review(review_id):
    reviews = _load_json(REVIEWS_FILE)
    rev = next((r for r in reviews if r["review_id"] == review_id), None)
    if not rev:
        return jsonify({"error": "Review case not found"}), 404

    data = request.get_json() or {}
    res_code = data.get("resolution_code")
    res_notes = data.get("resolution_notes")
    actor_id = request.headers.get("X-Actor-Id", "compliance_reviewer_01")
    actor_role = request.headers.get("X-Actor-Role", "Risk / Compliance Reviewer")

    # Gating rule: review closure mandates resolution code and non-empty notes
    if not res_code or not res_notes or not str(res_notes).strip():
        return jsonify({
            "error": "Resolution code and non-empty resolution notes are mandatory to close a review case."
        }), 422

    prev_status = rev["review_status"]
    rev["review_status"] = "COMPLETED"
    rev["resolution_code"] = res_code
    rev["resolution_notes"] = res_notes.strip()
    rev["closed_at"] = datetime.utcnow().isoformat()
    rev["assigned_reviewer_id"] = actor_id

    _save_json(REVIEWS_FILE, reviews)

    # Audit log
    audits = _load_json(AUDIT_FILE)
    audits.append({
        "audit_event_id": len(audits) + 1,
        "entity_type": "REVIEW",
        "entity_id": review_id,
        "event_type": "REVIEW_CLOSED",
        "actor_id": actor_id,
        "event_timestamp": datetime.utcnow().isoformat(),
        "previous_values": {"review_status": prev_status},
        "new_values": {"review_status": "COMPLETED", "resolution_code": res_code},
        "reason": f"Review closure: {res_code} - {res_notes}",
        "correlation_id": f"CORR-{rev['customer_id']}"
    })
    _save_json(AUDIT_FILE, audits)

    return jsonify({"success": True, "review": rev})
