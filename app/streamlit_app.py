import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
try:
    from app.components.helpers import render_role_selector, api_get
except ImportError:
    from components.helpers import render_role_selector, api_get

st.set_page_config(
    page_title="KYC Onboarding & Compliance Management System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_role_selector()

st.title("🛡️ KYC Onboarding & Compliance Management System")
st.markdown("""
Welcome to the enterprise **KYC Onboarding & Compliance Management System**.
This application tracks customer onboarding evidence, validates document completeness, manages risk ratings, schedules periodic reviews, detects document expirations, generates alerts, handles exceptions, and maintains a traceable audit history.

### Application Navigation
Use the sidebar navigation to access each module:
1. **Dashboard:** Live executive compliance metrics, completeness distributions, alert queues, and onboarding trends.
2. **Customer Management:** Comprehensive search, risk profiles, UBO ownership trees, and customer 360 drawers.
3. **Onboarding Workflow:** Step-by-step evidence collection, mandatory document validation, and approval gating.
4. **Document Management:** Document inventory, issue/expiry tracking, verification workflows, and reasons.
5. **Review Management:** Risk-based periodic review scheduler (Low 24m, Medium 12m, High 6m) and closure signoff.
6. **Exceptions Centre:** Independent anomaly detection engine detecting all 5 controlled anomaly scenarios.
7. **Alerts Centre:** Expiry alerts (30d, 15d, 7d escalation), overdue reviews, and missing evidence warnings.
8. **Audit Trail:** Immutable audit logs with actor tracking, entity deltas, and correlation IDs.
9. **Data Quality & Evaluation:** Precision/Recall metrics, foreign-key integrity reports, reproducibility checksums, and dataset exports.
""")

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.info("**Backend Status**\nConnected to Flask REST API (`http://localhost:5000`)")
with col2:
    st.info("**Database Engine**\nMySQL 8.0 InnoDB with foreign key integrity & migrations")
with col3:
    st.info("**Active User Role**\n`" + st.session_state.get("current_role", "Operations Analyst") + "`")
