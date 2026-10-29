from flask import Flask, jsonify
from backend.config import Config
from backend.extensions import db, migrate, cors
from backend.routes.customers import customers_bp
from backend.routes.documents import documents_bp
from backend.routes.reviews import reviews_bp
from backend.routes.alerts import alerts_bp
from backend.routes.exceptions import exceptions_bp
from backend.routes.audit import audit_bp
from backend.routes.metrics import metrics_bp
from backend.routes.generator import generator_bp
from backend.routes.exports import exports_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register API Blueprints
    app.register_blueprint(customers_bp, url_prefix="/api/v1/customers")
    app.register_blueprint(documents_bp, url_prefix="/api/v1/documents")
    app.register_blueprint(reviews_bp, url_prefix="/api/v1/reviews")
    app.register_blueprint(alerts_bp, url_prefix="/api/v1/alerts")
    app.register_blueprint(exceptions_bp, url_prefix="/api/v1/exceptions")
    app.register_blueprint(audit_bp, url_prefix="/api/v1/audit")
    app.register_blueprint(metrics_bp, url_prefix="/api/v1/metrics")
    app.register_blueprint(generator_bp, url_prefix="/api/v1/generator")
    app.register_blueprint(exports_bp, url_prefix="/api/v1/exports")

    # OpenAPI documentation endpoint
    @app.route("/api/v1/docs", methods=["GET"])
    def get_openapi_spec():
        return jsonify({
            "openapi": "3.0.3",
            "info": {
                "title": "KYC Onboarding & Compliance Management System REST API",
                "version": "1.0.0",
                "description": "Production REST API for customer KYC onboarding, document completeness, risk rating, periodic review scheduling, expiry alerts, and immutable audit trails."
            },
            "servers": [{"url": "/api/v1"}],
            "paths": {
                "/customers": {
                    "get": {"summary": "List customers with search, status, and pagination"},
                    "post": {"summary": "Create customer onboarding record"}
                },
                "/customers/{id}": {
                    "get": {"summary": "Get customer 360 profile with completeness percentage"}
                },
                "/customers/{id}/decision": {
                    "post": {"summary": "Evaluate and apply onboarding approval/rejection decision"}
                },
                "/documents": {
                    "get": {"summary": "List customer evidence documents"}
                },
                "/documents/{id}/verify": {
                    "post": {"summary": "Record document verification outcome"}
                },
                "/reviews": {
                    "get": {"summary": "List periodic and triggered compliance reviews"}
                },
                "/reviews/{id}/close": {
                    "post": {"summary": "Close review case with mandatory resolution code and notes"}
                },
                "/alerts": {
                    "get": {"summary": "List expiry, review, and compliance alerts"}
                },
                "/alerts/{id}/resolve": {
                    "post": {"summary": "Resolve alert with remediation notes"}
                },
                "/exceptions": {
                    "get": {"summary": "Independent anomaly detection across operational records"}
                },
                "/exceptions/remediate": {
                    "post": {"summary": "Execute remediation workflow for detected anomaly"}
                },
                "/audit": {
                    "get": {"summary": "Query immutable audit history"}
                },
                "/metrics": {
                    "get": {"summary": "Get compliance rates, precision, recall, and integrity stats"}
                },
                "/generator/run": {
                    "post": {"summary": "Trigger deterministic synthetic data generation"}
                }
            }
        })

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "service": "kyc-compliance-backend"})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
