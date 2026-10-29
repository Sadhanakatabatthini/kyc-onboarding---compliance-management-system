from flask import Blueprint, request, jsonify
from datetime import datetime, date
import json
import os

documents_bp = Blueprint("documents", __name__)

DOCS_FILE = "data/generated/documents.json"
VER_FILE = "data/generated/verifications.json"
AUDIT_FILE = "data/generated/audit_events.json"

def _load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@documents_bp.route("", methods=["GET"])
def list_documents():
    docs = _load_json(DOCS_FILE)
    cid = request.args.get("customer_id")
    status = request.args.get("status")
    doc_type = request.args.get("document_type")

    filtered = docs
    if cid:
        filtered = [d for d in filtered if d["customer_id"] == cid]
    if status:
        filtered = [d for d in filtered if d["document_status"] == status]
    if doc_type:
        filtered = [d for d in filtered if d["document_type"] == doc_type]

    return jsonify({"items": filtered, "total": len(filtered)})

@documents_bp.route("/<document_id>/verify", methods=["POST"])
def verify_document(document_id):
    docs = _load_json(DOCS_FILE)
    doc = next((d for d in docs if d["document_id"] == document_id), None)
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    data = request.get_json() or {}
    outcome = data.get("verification_status")  # PASSED, FAILED, PENDING_MORE_INFO
    reviewer_id = request.headers.get("X-Actor-Id", data.get("reviewer_id", "operations_analyst_01"))
    reason_code = data.get("reason_code", "MANUAL_INSPECTION")
    comments = data.get("comments", "")

    if outcome not in ["PASSED", "FAILED", "PENDING_MORE_INFO"]:
        return jsonify({"error": "Invalid verification_status"}), 400

    vers = _load_json(VER_FILE)
    vid = f"VER-{document_id}-{len(vers) + 1}"
    prev_status = doc["document_status"]

    # If verification PASSED, check if document is expired
    today = date.today()
    exp = doc.get("expiry_date")
    if exp and date.fromisoformat(exp) < today:
        doc["document_status"] = "EXPIRED"
    elif outcome == "PASSED":
        doc["document_status"] = "VALID"
    elif outcome == "FAILED":
        doc["document_status"] = "INVALID"

    verification = {
        "verification_id": vid,
        "document_id": document_id,
        "verification_status": outcome,
        "verification_method": data.get("verification_method", "MANUAL_ANALYST"),
        "verification_timestamp": datetime.utcnow().isoformat(),
        "reviewer_id": reviewer_id,
        "reason_code": reason_code,
        "comments": comments,
        "previous_status": prev_status,
        "created_at": datetime.utcnow().isoformat()
    }
    vers.append(verification)

    _save_json(DOCS_FILE, docs)
    _save_json(VER_FILE, vers)

    # Audit log
    audits = _load_json(AUDIT_FILE)
    audits.append({
        "audit_event_id": len(audits) + 1,
        "entity_type": "DOCUMENT",
        "entity_id": document_id,
        "event_type": "VERIFICATION_SUBMITTED",
        "actor_id": reviewer_id,
        "event_timestamp": datetime.utcnow().isoformat(),
        "previous_values": {"document_status": prev_status},
        "new_values": {"document_status": doc["document_status"], "verification_status": outcome},
        "reason": f"Verification completed: {reason_code} - {comments}",
        "correlation_id": f"CORR-{doc['customer_id']}"
    })
    _save_json(AUDIT_FILE, audits)

    return jsonify({"success": True, "document": doc, "verification": verification})
