from datetime import datetime
from backend.extensions import db
from backend.models.base import BaseModel

class Owner(BaseModel):
    __tablename__ = "owners"

    owner_id = db.Column(db.String(32), primary_key=True)  # e.g. OWN-00001
    owner_reference = db.Column(db.String(128), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    beneficial_ownerships = db.relationship("BeneficialOwnership", back_populates="owner", cascade="all, delete-orphan", lazy="dynamic")


class BeneficialOwnership(BaseModel):
    __tablename__ = "beneficial_ownership"

    ownership_id = db.Column(db.String(32), primary_key=True)  # e.g. UBO-00001
    business_customer_id = db.Column(db.String(32), db.ForeignKey("customers.customer_id"), nullable=False, index=True)
    owner_id = db.Column(db.String(32), db.ForeignKey("owners.owner_id"), nullable=False, index=True)
    ownership_percentage = db.Column(db.Numeric(5, 2), nullable=False)  # DECIMAL e.g. 25.50
    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date, nullable=True)
    verification_status = db.Column(db.String(32), nullable=False, default="VERIFIED", index=True)  # VERIFIED, PENDING, DISCREPANCY

    business_customer = db.relationship("Customer", back_populates="beneficial_ownerships")
    owner = db.relationship("Owner", back_populates="beneficial_ownerships")
