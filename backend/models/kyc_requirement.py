from backend.extensions import db
from backend.models.base import BaseModel

class KYCRequirement(BaseModel):
    __tablename__ = "kyc_requirements"

    requirement_id = db.Column(db.String(32), primary_key=True)  # e.g. KYC-2026-000001
    requirement_code = db.Column(db.String(64), nullable=False, index=True)
    customer_type_id = db.Column(db.Integer, db.ForeignKey("customer_types.customer_type_id"), nullable=False, index=True)
    applicable_risk_level = db.Column(db.String(16), nullable=False, default="ALL", index=True)  # ALL, LOW, MEDIUM, HIGH
    document_type = db.Column(db.String(64), nullable=False)
    mandatory_flag = db.Column(db.Boolean, default=True, nullable=False)
    effective_from = db.Column(db.Date, nullable=False, index=True)
    effective_to = db.Column(db.Date, nullable=True, index=True)
    active_status = db.Column(db.Boolean, default=True, nullable=False)

    customer_type = db.relationship("CustomerType", back_populates="requirements")
    documents = db.relationship("Document", back_populates="requirement", lazy="dynamic")
