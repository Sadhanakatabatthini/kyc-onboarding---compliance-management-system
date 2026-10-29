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

st.set_page_config(page_title="Exceptions Centre | KYC Compliance", page_icon="🚨", layout="wide")
render_role_selector()

st.title("🚨 Compliance Exceptions Centre & Anomaly Remediation")
st.markdown("Independent algorithmic discovery evaluating operational records across the 5 controlled compliance anomaly types.")

resp = api_get("exceptions")
if not resp:
    st.info("Scanning for exceptions...")
    st.stop()

exceptions = resp.get("items", [])
st.caption(f"Detected Anomaly Count: **{len(exceptions)}**")

if exceptions:
    df = pd.DataFrame(exceptions)
    st.dataframe(df[["anomaly_type", "severity", "affected_entity_type", "affected_entity_id", "customer_id", "description"]], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🛠️ Remediation Workflow")
    sel_idx = st.selectbox("Select Anomaly to Remediate:", range(len(exceptions)), format_func=lambda i: f"[{exceptions[i]['severity']}] {exceptions[i]['anomaly_type']} - Entity: {exceptions[i]['affected_entity_id']}")

    sel = exceptions[sel_idx]
    st.warning(f"**Anomaly:** {sel['anomaly_type']}\n\n**Description:** {sel['description']}\n\n**Expected Action:** {sel['expected_action']}")

    notes = st.text_input("Compliance Remediation Justification:", value="Actioned in accordance with regulatory rectification procedures.")
    if st.button("Apply Remediation & Record Audit Trail", type="primary"):
        payload = {
            "anomaly_type": sel["anomaly_type"],
            "entity_id": sel["affected_entity_id"],
            "notes": notes
        }
        res, code = api_post("exceptions/remediate", payload)
        if code == 200:
            st.success(f"Remediation successfully applied! {res.get('message')}")
            st.rerun()
        else:
            st.error(res.get("error", "Remediation failed"))
else:
    st.success("No anomalies currently detected across operational records.")
