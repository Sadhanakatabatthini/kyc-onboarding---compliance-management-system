from backend.extensions import db
from backend.models.base import BaseModel

class CustomerType(BaseModel):
    __tablename__ = "customer_types"

    customer_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    active_status = db.Column(db.Boolean, default=True, nullable=False)

    customers = db.relationship("Customer", back_populates="customer_type", lazy="dynamic")
    requirements = db.relationship("KYCRequirement", back_populates="customer_type", lazy="dynamic")
