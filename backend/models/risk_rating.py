from backend.extensions import db
from backend.models.base import BaseModel

class RiskRating(BaseModel):
    __tablename__ = "risk_ratings"

    risk_rating_id = db.Column(db.String(32), primary_key=True)  # e.g. RSK-CUS-000001-01
    customer_id = db.Column(db.String(32), db.ForeignKey("customers.customer_id"), nullable=False, index=True)
    risk_level = db.Column(db.String(16), nullable=False, index=True)  # LOW, MEDIUM, HIGH
    risk_score = db.Column(db.Numeric(5, 2), nullable=False)  # 0.00 to 100.00
    reason_codes = db.Column(db.JSON, nullable=False)  # JSON array of reasons
    assessment_date = db.Column(db.Date, nullable=False, index=True)
    effective_from = db.Column(db.Date, nullable=False)
    effective_to = db.Column(db.Date, nullable=True)
    assessed_by = db.Column(db.String(64), nullable=False)

    customer = db.relationship("Customer", back_populates="risk_ratings")
