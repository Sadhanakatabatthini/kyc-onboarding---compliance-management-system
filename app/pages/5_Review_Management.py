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

st.set_page_config(page_title="Review Management | KYC Compliance", page_icon="📅", layout="wide")
render_role_selector()

st.title("📅 Compliance Review Case Management")

status_filter = st.selectbox("Filter Review Status:", ["ALL", "OVERDUE", "OPEN", "IN_PROGRESS", "COMPLETED"])
params = {}
if status_filter != "ALL":
    params["status"] = status_filter

resp = api_get("reviews", params=params)
if not resp:
    st.info("Loading review cases...")
    st.stop()

reviews = resp.get("items", [])
st.caption(f"Total reviews: {len(reviews)}")

if reviews:
    df = pd.DataFrame(reviews)
    st.dataframe(df[["review_id", "customer_id", "review_type", "due_date", "review_status", "assigned_reviewer_id", "resolution_code", "closed_at"]], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("✍️ Review Resolution Signoff (Mandatory Gating)")
    open_cases = [r for r in reviews if r["review_status"] != "COMPLETED"]
    if open_cases:
        sel_rev_id = st.selectbox("Select Active Case to resolve:", [r["review_id"] for r in open_cases])
        sel_rev = next(r for r in open_cases if r["review_id"] == sel_rev_id)

        st.info(f"Resolving Review: **{sel_rev['review_id']}** for Customer: `{sel_rev['customer_id']}` | Type: `{sel_rev['review_type']}` | Due Date: `{sel_rev['due_date']}`")

        with st.form("close_review_form"):
            r_code = st.selectbox("Resolution Outcome Code:", ["APPROVED_RETAIN", "DERISK_OFFBOARD", "EXCEPTION_GRANTED"])
            r_notes = st.text_area("Mandatory Resolution Notes (Compliance Justification):", placeholder="Enter comprehensive justification for case closure...")
            submit_close = st.form_submit_button("Close Review Case", type="primary")

            if submit_close:
                if not r_notes.strip():
                    st.error("Resolution notes are mandatory to close compliance reviews.")
                else:
                    payload = {
                        "resolution_code": r_code,
                        "resolution_notes": r_notes.strip()
                    }
                    res, code = api_post(f"reviews/{sel_rev_id}/close", payload)
                    if code == 200:
                        st.success(f"Review case {sel_rev_id} successfully closed!")
                        st.rerun()
                    else:
                        st.error(res.get("error", "Failed to close review case"))
    else:
        st.success("No unclosed review cases in the current filter.")
