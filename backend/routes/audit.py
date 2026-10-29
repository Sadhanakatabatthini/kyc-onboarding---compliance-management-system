from flask import Blueprint, request, jsonify
import json
import os

audit_bp = Blueprint("audit", __name__)

AUDIT_FILE = "data/generated/audit_events.json"

def _load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@audit_bp.route("", methods=["GET"])
def list_audit_events():
    events = _load_json(AUDIT_FILE)
    entity_type = request.args.get("entity_type")
    entity_id = request.args.get("entity_id")
    event_type = request.args.get("event_type")
    actor_id = request.args.get("actor_id")
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 50))

    filtered = events
    if entity_type:
        filtered = [e for e in filtered if e["entity_type"] == entity_type]
    if entity_id:
        filtered = [e for e in filtered if str(e["entity_id"]) == str(entity_id)]
    if event_type:
        filtered = [e for e in filtered if e["event_type"] == event_type]
    if actor_id:
        filtered = [e for e in filtered if e["actor_id"] == actor_id]

    # Chronological sort (newest first)
    filtered = sorted(filtered, key=lambda x: x.get("event_timestamp", ""), reverse=True)

    total = len(filtered)
    start = (page - 1) * page_size
    items = filtered[start:start + page_size]

    return jsonify({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    })
