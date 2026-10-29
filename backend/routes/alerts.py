from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import os

alerts_bp = Blueprint("alerts", __name__)

ALERTS_FILE = "data/generated/alerts.json"
AUDIT_FILE = "data/generated/audit_events.json"

def _load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@alerts_bp.route("", methods=["GET"])
def list_alerts():
    alerts = _load_json(ALERTS_FILE)
    status = request.args.get("status")
    severity = request.args.get("severity")
    atype = request.args.get("alert_type")
    cid = request.args.get("customer_id")

    filtered = alerts
    if status:
        filtered = [a for a in filtered if a["alert_status"] == status]
    if severity:
        filtered = [a for a in filtered if a["severity"] == severity]
    if atype:
        filtered = [a for a in filtered if a["alert_type"] == atype]
    if cid:
        filtered = [a for a in filtered if a["customer_id"] == cid]

    return jsonify({"items": filtered, "total": len(filtered)})

@alerts_bp.route("/<alert_id>/resolve", methods=["POST"])
def resolve_alert(alert_id):
    alerts = _load_json(ALERTS_FILE)
    alert = next((a for a in alerts if a["alert_id"] == alert_id), None)
    if not alert:
        return jsonify({"error": "Alert not found"}), 404

    data = request.get_json() or {}
    notes = data.get("resolution_notes", "Remediation verified by compliance analyst.")
    actor_id = request.headers.get("X-Actor-Id", "analyst_01")

    prev_status = alert["alert_status"]
    alert["alert_status"] = "RESOLVED"
    alert["resolved_at"] = datetime.utcnow().isoformat()
    alert["resolution_notes"] = notes

    _save_json(ALERTS_FILE, alerts)

    # Audit log
    audits = _load_json(AUDIT_FILE)
    audits.append({
        "audit_event_id": len(audits) + 1,
        "entity_type": "ALERT",
        "entity_id": alert_id,
        "event_type": "ALERT_RESOLVED",
        "actor_id": actor_id,
        "event_timestamp": datetime.utcnow().isoformat(),
        "previous_values": {"alert_status": prev_status},
        "new_values": {"alert_status": "RESOLVED"},
        "reason": notes,
        "correlation_id": f"CORR-{alert['customer_id']}"
    })
    _save_json(AUDIT_FILE, audits)

    return jsonify({"success": True, "alert": alert})
