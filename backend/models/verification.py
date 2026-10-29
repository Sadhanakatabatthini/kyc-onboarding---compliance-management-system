from datetime import datetime
from backend.extensions import db
from backend.models.base import BaseModel

class Verification(BaseModel):
    __tablename__ = "verifications"

    verification_id = db.Column(db.String(32), primary_key=True)  # e.g. VER-DOC-000001-1
    document_id = db.Column(db.String(32), db.ForeignKey("documents.document_id"), nullable=False, index=True)
    verification_status = db.Column(db.String(32), nullable=False, index=True)  # PASSED, FAILED, PENDING_MORE_INFO
    verification_method = db.Column(db.String(64), nullable=False)  # AUTOMATED_OCR, MANUAL_ANALYST, THIRD_PARTY_BUREAU
    verification_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    reviewer_id = db.Column(db.String(64), nullable=False)
    reason_code = db.Column(db.String(64), nullable=True)
    comments = db.Column(db.Text, nullable=True)
    previous_status = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    document = db.relationship("Document", back_populates="verifications")
