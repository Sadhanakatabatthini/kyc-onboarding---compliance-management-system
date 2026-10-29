from datetime import datetime
from backend.extensions import db
from backend.models.base import BaseModel

class AuditEvent(BaseModel):
    __tablename__ = "audit_events"

    audit_event_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    entity_type = db.Column(db.String(64), nullable=False, index=True)  # CUSTOMER, DOCUMENT, REVIEW, ALERT, BENEFICIAL_OWNERSHIP
    entity_id = db.Column(db.String(64), nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False, index=True)  # STATUS_CHANGE, VERIFICATION_SUBMITTED, APPROVAL_GRANTED, APPROVAL_REJECTED, ANOMALY_RESOLVED, OWNERSHIP_UPDATED
    actor_id = db.Column(db.String(64), nullable=False, index=True)
    event_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    previous_values = db.Column(db.JSON, nullable=True)
    new_values = db.Column(db.JSON, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    correlation_id = db.Column(db.String(64), nullable=True, index=True)
