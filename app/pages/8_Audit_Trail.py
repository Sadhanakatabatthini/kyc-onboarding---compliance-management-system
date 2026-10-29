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
    from app.components.helpers import render_role_selector, api_get
except ImportError:
    from components.helpers import render_role_selector, api_get

st.set_page_config(page_title="Audit Trail | KYC Compliance", page_icon="📜", layout="wide")
render_role_selector()

st.title("📜 Immutable Regulatory Audit Trail")
st.markdown("Chronological, tamper-evident audit records capturing every state change, document evaluation, and approval decision.")

c1, c2 = st.columns(2)
etype_filter = c1.selectbox("Filter Entity Type:", ["ALL", "CUSTOMER", "DOCUMENT", "REVIEW", "ALERT", "BENEFICIAL_OWNERSHIP"])
event_filter = c2.text_input("Filter by Event Type:", placeholder="e.g. STATUS_TRANSITION or APPROVAL_GRANTED")

params = {"page_size": 100}
if etype_filter != "ALL":
    params["entity_type"] = etype_filter
if event_filter:
    params["event_type"] = event_filter.strip()

resp = api_get("audit", params=params)
if not resp:
    st.info("Loading audit history...")
    st.stop()

events = resp.get("items", [])
st.caption(f"Showing latest {len(events)} events (immutable history)")

if events:
    df = pd.DataFrame(events)
    st.dataframe(df[["audit_event_id", "event_timestamp", "entity_type", "entity_id", "event_type", "actor_id", "reason", "correlation_id"]], use_container_width=True, hide_index=True)


