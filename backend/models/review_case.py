from datetime import datetime
from backend.extensions import db
from backend.models.base import BaseModel

class ReviewCase(BaseModel):
    __tablename__ = "review_cases"

    review_id = db.Column(db.String(32), primary_key=True)  # e.g. REV-CUS-000001-2026
    customer_id = db.Column(db.String(32), db.ForeignKey("customers.customer_id"), nullable=False, index=True)
    review_type = db.Column(db.String(32), nullable=False, index=True)  # PERIODIC_LOW, PERIODIC_MEDIUM, PERIODIC_HIGH, TRIGGERED_EXCEPTION
    opened_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    due_date = db.Column(db.Date, nullable=False, index=True)
    review_status = db.Column(db.String(32), nullable=False, default="OPEN", index=True)  # OPEN, IN_PROGRESS, PENDING_CUSTOMER, COMPLETED, OVERDUE, ESCALATED
    assigned_reviewer_id = db.Column(db.String(64), nullable=True)
    resolution_code = db.Column(db.String(64), nullable=True)  # APPROVED_RETAIN, DERISK_OFFBOARD, EXCEPTION_GRANTED
    resolution_notes = db.Column(db.Text, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    customer = db.relationship("Customer", back_populates="review_cases")
    alerts = db.relationship("Alert", back_populates="review_case", cascade="all, delete-orphan", lazy="dynamic")
