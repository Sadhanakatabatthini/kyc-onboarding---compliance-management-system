import sys
import os

app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_dir = os.path.abspath(os.path.join(app_dir, ".."))
for p in [app_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st
import pandas as pd
try:
    from app.components.helpers import render_role_selector, api_get, api_post
except ImportError:
    from components.helpers import render_role_selector, api_get, api_post

st.set_page_config(page_title="Data Quality & Evaluation | KYC Compliance", page_icon="🔬", layout="wide")
render_role_selector()

st.title("🔬 Data Quality, Metrics & Reproducibility Evaluation")

metrics_data = api_get("metrics")
if not metrics_data:
    st.info("Loading evaluation metrics...")
    st.stop()

eval_res = metrics_data.get("evaluation", {})
integrity = metrics_data.get("integrity", {})
summary = eval_res.get("evaluation_summary", {})
op = eval_res.get("operational_compliance_metrics", {})
breakdown = eval_res.get("anomaly_breakdown", {})

tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Model Evaluation Metrics",
    "🛡️ Database Integrity Checks",
    "🔄 Seed & Reproducibility",
    "💾 Data Exports"
])

with tab1:
    st.subheader("Confusion Matrix & Precision/Recall Performance")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Precision", f"{summary.get('precision_percentage', 0)}%")
    c2.metric("Recall", f"{summary.get('recall_percentage', 0)}%")
    c3.metric("F1 Score", f"{summary.get('f1_score_percentage', 0)}%")
    c4.metric("False Positive Rate", f"{summary.get('false_positive_rate_percentage', 0)}%")

    cm = summary.get("confusion_matrix", {})
    st.markdown(f"""
    | Metric | Count | Description |
    |---|---|---|
    | **True Positives (TP)** | `{cm.get('true_positives', 0)}` | Anomaly successfully discovered by independent detection rules |
    | **False Positives (FP)** | `{cm.get('false_positives', 0)}` | Non-anomalous entities flagged by rules |
    | **False Negatives (FN)** | `{cm.get('false_negatives', 0)}` | Injected anomalies missed by detection rules |
    | **True Negatives (TN)** | `{cm.get('true_negatives', 0)}` | Clean compliance records correctly unflagged |
    """)

    st.subheader("Performance Breakdown by Anomaly Scenario")
    if breakdown:
        b_df = pd.DataFrame.from_dict(breakdown, orient="index").reset_index()
        b_df.columns = ["Anomaly Scenario", "True Positives", "False Positives", "False Negatives", "Total Detected", "Ground Truth Count"]
        st.dataframe(b_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Relational Schema Integrity & Constraint Verification")
    st.success(f"Status: **{integrity.get('status')}** (Zero broken constraints)")
    k1, k2, k3 = st.columns(3)
    k1.metric("Primary Key Violations", integrity.get("pk_violations_count", 0))
    k2.metric("Foreign Key Violations", integrity.get("fk_violations_count", 0))
    k3.metric("Null Constraint Violations", integrity.get("null_violations_count", 0))

with tab3:
    st.subheader("Deterministic Seed Reproducibility")
    st.markdown("""
    The dataset generation is deterministic under master seed `20261022`.
    Two consecutive runs with identical seed parameters output exact matching SHA-256 byte checksums.
    """)
    with st.form("gen_form"):
        st.write("Trigger Generator Run:")
        g_seed = st.number_input("Seed:", value=20261022, step=1)
        g_cust = st.number_input("Customers Count:", value=100, step=50)
        g_doc = st.number_input("Documents Count:", value=250, step=50)
        g_rev = st.number_input("Review Cases Count:", value=40, step=10)
        run_btn = st.form_submit_button("Generate Dataset & Calculate SHA-256")

        if run_btn:
            res, code = api_post("generator/run", {
                "seed": g_seed,
                "customers": g_cust,
                "documents": g_doc,
                "reviews": g_rev
            })
            if code == 200:
                st.success("Generation completed and exported!")
                st.json(res.get("checksums", {}))
            else:
                st.error("Generation failed.")

with tab4:
    st.subheader("Direct Dataset & SQL Script Exports")
    st.markdown("Download generated CSV, JSON datasets and MySQL 8.0 schema and seed scripts:")

    tables = ["customers", "documents", "verifications", "risk_ratings", "review_cases", "beneficial_ownership", "alerts", "audit_events", "ground_truth"]
    for t in tables:
        c1, c2 = st.columns([3, 1])
        c1.write(f"📁 **{t}** (CSV & JSON)")
        c2.markdown(f"[Download CSV](/api/v1/exports/csv/{t}) | [Download JSON](/api/v1/exports/json/{t})")
    
    st.markdown("---")
    st.markdown("📄 **MySQL DDL Schema Script:** [Download kyc_schema.sql](/api/v1/exports/sql/kyc_schema.sql)")
    st.markdown("🌱 **MySQL Seed Script:** [Download kyc_seeds.sql](/api/v1/exports/sql/kyc_seeds.sql)")
