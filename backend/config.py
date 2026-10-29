import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "kyc-compliance-secret-key-2026")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        "sqlite:///kyc_compliance.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    } if "mysql" in os.getenv("DATABASE_URL", "") else {}
    
    DEFAULT_SEED = int(os.getenv("DEFAULT_SEED", "20261022"))
    API_TITLE = "KYC Onboarding & Compliance Management API"
    API_VERSION = "v1"
