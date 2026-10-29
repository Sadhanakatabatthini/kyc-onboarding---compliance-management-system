from flask import Blueprint, send_from_directory, jsonify
import os

exports_bp = Blueprint("exports", __name__)

DATA_DIR = os.path.abspath("data/generated")
GT_DIR = os.path.abspath("data/ground_truth")
SQL_DIR = os.path.abspath("exports")

@exports_bp.route("/csv/<table_name>", methods=["GET"])
def export_csv(table_name):
    filename = f"{table_name}.csv"
    if table_name == "ground_truth":
        return send_from_directory(GT_DIR, filename, as_attachment=True)
    return send_from_directory(DATA_DIR, filename, as_attachment=True)

@exports_bp.route("/json/<table_name>", methods=["GET"])
def export_json(table_name):
    filename = f"{table_name}.json"
    if table_name == "ground_truth":
        return send_from_directory(GT_DIR, filename, as_attachment=True)
    return send_from_directory(DATA_DIR, filename, as_attachment=True)

@exports_bp.route("/sql/<file_name>", methods=["GET"])
def export_sql(file_name):
    if not file_name.endswith(".sql"):
        file_name += ".sql"
    return send_from_directory(SQL_DIR, file_name, as_attachment=True)
