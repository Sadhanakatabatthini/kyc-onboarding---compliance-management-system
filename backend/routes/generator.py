from flask import Blueprint, request, jsonify
from generator.generate import generate_dataset, export_to_files

generator_bp = Blueprint("generator", __name__)

@generator_bp.route("/run", methods=["POST"])
def trigger_generator():
    data = request.get_json() or {}
    seed = int(data.get("seed", 20261022))
    customers = int(data.get("customers", 100))
    documents = int(data.get("documents", 250))
    reviews = int(data.get("reviews", 40))
    inject_anomalies = bool(data.get("inject_anomalies", True))

    dataset = generate_dataset(
        seed=seed,
        num_customers=customers,
        target_business_count=max(1, customers // 8),
        num_documents=documents,
        num_reviews=reviews,
        inject_controlled_anomalies=inject_anomalies
    )
    checksums = export_to_files(dataset)

    return jsonify({
        "success": True,
        "seed": seed,
        "counts": {
            "customers": len(dataset["customers"]),
            "documents": len(dataset["documents"]),
            "reviews": len(dataset["review_cases"]),
            "alerts": len(dataset["alerts"]),
            "ground_truth_anomalies": len(dataset["ground_truth"])
        },
        "checksums": checksums
    })
