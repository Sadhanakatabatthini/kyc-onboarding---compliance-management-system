from datetime import datetime
from backend.extensions import db
from backend.models.base import BaseModel

class Document(BaseModel):
    __tablename__ = "documents"

    document_id = db.Column(db.String(32), primary_key=True)  # e.g. DOC-CUS-000001-001
    customer_id = db.Column(db.String(32), db.ForeignKey("customers.customer_id"), nullable=False, index=True)
    requirement_id = db.Column(db.String(32), db.ForeignKey("kyc_requirements.requirement_id"), nullable=True, index=True)
    document_type = db.Column(db.String(64), nullable=False, index=True)
    issue_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True, index=True)
    submission_date = db.Column(db.Date, nullable=False)
    document_status = db.Column(db.String(32), nullable=False, default="SUBMITTED", index=True)  # SUBMITTED, VALID, EXPIRED, INVALID, REJECTED
    document_reference = db.Column(db.String(128), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    customer = db.relationship("Customer", back_populates="documents")
    requirement = db.relationship("KYCRequirement", back_populates="documents")
    verifications = db.relationship("Verification", back_populates="document", cascade="all, delete-orphan", lazy="dynamic")
    alerts = db.relationship("Alert", back_populates="document", cascade="all, delete-orphan", lazy="dynamic")
