from datetime import date, timedelta

# Configurable periodic review intervals in months
REVIEW_INTERVALS_MONTHS = {
    "LOW": 24,       # Low risk: 24 months
    "MEDIUM": 12,    # Medium risk: 12 months
    "HIGH": 6        # High risk: 6 months (Enhanced Due Diligence)
}

# Configurable alert lead times in days
EXPIRY_ALERT_WINDOWS_DAYS = [30, 15, 7]

def add_months_approx(start_date: date, months: int) -> date:
    # Deterministic calendar addition: approximate 30.4375 days or day clamping
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    # Day clamping for short months
    day = min(start_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)

def calculate_review_due_date(risk_level: str, from_date: date) -> date:
    months = REVIEW_INTERVALS_MONTHS.get(risk_level.upper(), 12)
    return add_months_approx(from_date, months)

def determine_expiry_alert_tier(days_remaining: int) -> str:
    """
    Returns alert severity and type for a given day offset to expiry.
    """
    if days_remaining < 0:
        return "DOCUMENT_EXPIRED", "CRITICAL"
    elif days_remaining <= 7:
        return "DOCUMENT_EXPIRY_7D", "HIGH"
    elif days_remaining <= 15:
        return "DOCUMENT_EXPIRY_15D", "MEDIUM"
    elif days_remaining <= 30:
        return "DOCUMENT_EXPIRY_30D", "LOW"
    return None, None
