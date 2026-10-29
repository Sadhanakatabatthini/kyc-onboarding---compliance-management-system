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

st.set_page_config(page_title="Alerts Centre | KYC Compliance", page_icon="🔔", layout="wide")
render_role_selector()

st.title("🔔 Real-Time Compliance Alerts Centre")

c1, c2 = st.columns(2)
status_filter = c1.selectbox("Filter Alert Status:", ["ALL", "OPEN", "RESOLVED"])
sev_filter = c2.selectbox("Filter Severity:", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])

params = {}
if status_filter != "ALL":
    params["status"] = status_filter
if sev_filter != "ALL":
    params["severity"] = sev_filter

resp = api_get("alerts", params=params)
if not resp:
    st.info("Loading alerts...")
    st.stop()

alerts = resp.get("items", [])
st.caption(f"Showing {len(alerts)} alerts")

if alerts:
    df = pd.DataFrame(alerts)
    st.dataframe(df[["alert_id", "customer_id", "alert_type", "severity", "alert_status", "created_at", "due_at", "resolution_notes"]], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("✅ Alert Resolution")
    open_alerts = [a for a in alerts if a["alert_status"] == "OPEN"]
    if open_alerts:
        sel_aid = st.selectbox("Select Open Alert to resolve:", [a["alert_id"] for a in open_alerts])
        sel_a = next(a for a in open_alerts if a["alert_id"] == sel_aid)

        st.info(f"Target: `{sel_a['customer_id']}` | Type: `{sel_a['alert_type']}` | Severity: `{sel_a['severity']}`")
        res_notes = st.text_input("Resolution / Mitigation Notes:", value="Document updated by customer and verified; risk cleared.")
        if st.button("Resolve Alert", type="primary"):
            res, code = api_post(f"alerts/{sel_aid}/resolve", {"resolution_notes": res_notes})
            if code == 200:
                st.success(f"Alert {sel_aid} marked RESOLVED.")
                st.rerun()
            else:
                st.error("Failed to resolve alert.")
    else:
        st.success("No active open alerts matching current filter.")
