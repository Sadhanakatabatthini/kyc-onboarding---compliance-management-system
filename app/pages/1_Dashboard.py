import sys
import os

app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_dir = os.path.abspath(os.path.join(app_dir, ".."))
for p in [app_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st
import pandas as pd
import plotly.express as px
try:
    from app.components.helpers import render_role_selector, api_get
except ImportError:
    from components.helpers import render_role_selector, api_get

st.set_page_config(page_title="Dashboard | KYC Compliance", page_icon="📊", layout="wide")
render_role_selector()

st.title("📊 Executive Compliance Dashboard")

# Fetch metrics from API
metrics_data = api_get("metrics")
customers_resp = api_get("customers", params={"page_size": 1000})
alerts_resp = api_get("alerts")
reviews_resp = api_get("reviews")
exceptions_resp = api_get("exceptions")

if not metrics_data or not customers_resp:
    st.warning("Connecting to Flask REST API... If running standalone, ensure the backend is started.")
    st.stop()

eval_data = metrics_data.get("evaluation", {})
op_metrics = eval_data.get("operational_compliance_metrics", {})
customers = customers_resp.get("items", [])
alerts = alerts_resp.get("items", []) if alerts_resp else []
reviews = reviews_resp.get("items", []) if reviews_resp else []
exceptions = exceptions_resp.get("items", []) if exceptions_resp else []

# Top KPI row
c1, c2, c3, c4 = st.columns(4)
total_cust = len(customers)
approved_cust = sum(1 for c in customers if c.get("lifecycle_status") == "APPROVED")
pending_cust = sum(1 for c in customers if "PENDING" in c.get("lifecycle_status", ""))
open_alerts = sum(1 for a in alerts if a.get("alert_status") == "OPEN")

c1.metric("Total Customers", f"{total_cust:,}", "Live database")
c2.metric("Approved Accounts", f"{approved_cust:,}", f"{round(approved_cust/max(1, total_cust)*100, 1)}%")
c3.metric("Pending Onboarding", f"{pending_cust:,}", f"{round(pending_cust/max(1, total_cust)*100, 1)}%")
c4.metric("Active Compliance Alerts", f"{open_alerts:,}", "Requires action", delta_color="inverse")

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Customer Lifecycle Breakdown")
    status_counts = pd.Series([c["lifecycle_status"] for c in customers]).value_counts().reset_index()
    status_counts.columns = ["Lifecycle Status", "Count"]
    fig_status = px.pie(status_counts, names="Lifecycle Status", values="Count", hole=0.45,
                        color_discrete_sequence=px.colors.qualitative.Safe)
    fig_status.update_layout(margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_status, use_container_width=True)

with col_right:
    st.subheader("Alert Severity Distribution")
    if alerts:
        sev_counts = pd.Series([a["severity"] for a in alerts]).value_counts().reset_index()
        sev_counts.columns = ["Severity", "Count"]
        color_map = {"CRITICAL": "#ef4444", "HIGH": "#f97316", "MEDIUM": "#eab308", "LOW": "#3b82f6"}
        fig_sev = px.bar(sev_counts, x="Severity", y="Count", color="Severity", color_discrete_map=color_map)
        fig_sev.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_sev, use_container_width=True)
    else:
        st.info("No active alerts detected.")

st.markdown("---")
st.subheader("Independent Anomaly & Exception Detection Performance")
summary = eval_data.get("evaluation_summary", {})
m1, m2, m3, m4 = st.columns(4)
m1.metric("Detection Precision", f"{summary.get('precision_percentage', 0)}%")
m2.metric("Detection Recall", f"{summary.get('recall_percentage', 0)}%")
m3.metric("F1 Score", f"{summary.get('f1_score_percentage', 0)}%")
m4.metric("False Positive Rate", f"{summary.get('false_positive_rate_percentage', 0)}%")
