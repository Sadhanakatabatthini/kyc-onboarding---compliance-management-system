from datetime import datetime
from backend.extensions import db
from backend.models.base import BaseModel

class Customer(BaseModel):
    __tablename__ = "customers"

    customer_id = db.Column(db.String(32), primary_key=True)  # Deterministic ID e.g. CUS-000001
    customer_type_id = db.Column(db.Integer, db.ForeignKey("customer_types.customer_type_id"), nullable=False, index=True)
    legal_name = db.Column(db.String(255), nullable=False, index=True)
    country_code = db.Column(db.String(2), nullable=False, index=True)
    onboarding_date = db.Column(db.Date, nullable=False, index=True)
    lifecycle_status = db.Column(db.String(32), nullable=False, default="PENDING_EVIDENCE", index=True)
    onboarding_channel = db.Column(db.String(64), nullable=False, default="DIGITAL_PORTAL")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer_type = db.relationship("CustomerType", back_populates="customers")
    documents = db.relationship("Document", back_populates="customer", cascade="all, delete-orphan", lazy="dynamic")
    risk_ratings = db.relationship("RiskRating", back_populates="customer", cascade="all, delete-orphan", lazy="dynamic")
    review_cases = db.relationship("ReviewCase", back_populates="customer", cascade="all, delete-orphan", lazy="dynamic")
    beneficial_ownerships = db.relationship("BeneficialOwnership", back_populates="business_customer", cascade="all, delete-orphan", lazy="dynamic")
    alerts = db.relationship("Alert", back_populates="customer", cascade="all, delete-orphan", lazy="dynamic")
