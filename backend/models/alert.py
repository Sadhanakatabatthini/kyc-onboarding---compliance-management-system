from datetime import datetime
from backend.extensions import db
from backend.models.base import BaseModel

class Alert(BaseModel):
    __tablename__ = "alerts"

    alert_id = db.Column(db.String(32), primary_key=True)  # e.g. ALT-2026-000001
    customer_id = db.Column(db.String(32), db.ForeignKey("customers.customer_id"), nullable=False, index=True)
    document_id = db.Column(db.String(32), db.ForeignKey("documents.document_id"), nullable=True, index=True)
    review_id = db.Column(db.String(32), db.ForeignKey("review_cases.review_id"), nullable=True, index=True)
    alert_type = db.Column(db.String(64), nullable=False, index=True)
    # DOCUMENT_EXPIRY_30D, DOCUMENT_EXPIRY_15D, DOCUMENT_EXPIRY_7D, DOCUMENT_EXPIRED,
    # REVIEW_OVERDUE, BENEFICIAL_OWNERSHIP_OVER_100, MISSING_MANDATORY_EVIDENCE
    severity = db.Column(db.String(16), nullable=False, default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    due_at = db.Column(db.DateTime, nullable=True)
    alert_status = db.Column(db.String(32), default="OPEN", nullable=False, index=True)  # OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)

    customer = db.relationship("Customer", back_populates="alerts")
    document = db.relationship("Document", back_populates="alerts")
    review_case = db.relationship("ReviewCase", back_populates="alerts")
