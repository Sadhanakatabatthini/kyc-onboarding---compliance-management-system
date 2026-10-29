from flask import Blueprint, jsonify
from validation.metrics import compute_evaluation_metrics
from validation.integrity_checks import run_integrity_checks

metrics_bp = Blueprint("metrics", __name__)

@metrics_bp.route("", methods=["GET"])
def get_metrics():
    eval_metrics = compute_evaluation_metrics()
    integrity = run_integrity_checks()

    return jsonify({
        "evaluation": eval_metrics,
        "integrity": integrity
    })
