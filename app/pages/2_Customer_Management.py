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

st.set_page_config(page_title="Customer Management | KYC Compliance", page_icon="👥", layout="wide")
render_role_selector()

st.title("👥 Customer & Account Holder Management")

# Search and filter controls
c1, c2, c3 = st.columns([2, 1, 1])
search = c1.text_input("🔍 Search Customer ID or Legal Name:", placeholder="e.g. CUS-000001 or Apex")
status_filter = c2.selectbox("Lifecycle Status:", ["ALL", "APPROVED", "UNDER_REVIEW", "PENDING_VERIFICATION", "PENDING_EVIDENCE", "EXCEPTION", "REJECTED"])
type_filter = c3.selectbox("Entity Type:", ["ALL", "Individual", "Business"])

params = {"page_size": 100}
if search:
    params["search"] = search
if status_filter != "ALL":
    params["status"] = status_filter
if type_filter == "Individual":
    params["customer_type_id"] = 1
elif type_filter == "Business":
    params["customer_type_id"] = 2

resp = api_get("customers", params=params)
if not resp:
    st.info("Loading customers...")
    st.stop()

customers = resp.get("items", [])
st.caption(f"Showing {len(customers)} of {resp.get('total', len(customers))} matching records")

if customers:
    df = pd.DataFrame(customers)
    # Display table
    display_df = df[["customer_id", "legal_name", "country_code", "customer_type_id", "lifecycle_status", "onboarding_date", "onboarding_channel"]].copy()
    display_df["customer_type_id"] = display_df["customer_type_id"].map({1: "Individual", 2: "Business"})
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Customer 360 Detail View
    st.markdown("---")
    st.subheader("📋 Customer 360 Profile & Evidence Inspection")
    selected_cid = st.selectbox("Select Customer to inspect details:", [c["customer_id"] for c in customers])
    
    if selected_cid:
        cust_profile = api_get(f"customers/{selected_cid}")
        if cust_profile:
            c = cust_profile.get("customer", {})
            pct = cust_profile.get("completeness_percentage", 0)
            
            p1, p2, p3 = st.columns(3)
            p1.markdown(f"**Customer ID:** `{c.get('customer_id')}`\n\n**Legal Name:** {c.get('legal_name')}")
            p2.markdown(f"**Entity Type:** {'Business' if c.get('customer_type_id')==2 else 'Individual'}\n\n**Country:** {c.get('country_code')}")
            p3.markdown(f"**Status:** `{c.get('lifecycle_status')}`\n\n**KYC Completeness:** `{pct}%`")

            st.progress(min(1.0, pct / 100.0))

            tab1, tab2, tab3 = st.tabs(["📄 Submitted Documents", "👑 Beneficial Ownership", "⚠️ Missing Requirements"])
            with tab1:
                docs = cust_profile.get("documents", [])
                if docs:
                    st.dataframe(pd.DataFrame(docs)[["document_id", "document_type", "issue_date", "expiry_date", "document_status", "document_reference"]], use_container_width=True, hide_index=True)
                else:
                    st.info("No documents submitted yet.")

            with tab2:
                ubos = cust_profile.get("beneficial_ownership", [])
                if ubos:
                    st.dataframe(pd.DataFrame(ubos)[["ownership_id", "owner_id", "ownership_percentage", "verification_status"]], use_container_width=True, hide_index=True)
                else:
                    st.info("No beneficial ownership records (applicable for Business entities).")

            with tab3:
                miss = cust_profile.get("missing_requirements", [])
                if miss:
                    for m in miss:
                        st.error(f"Missing Mandatory Evidence: **{m.get('requirement_code')}** ({m.get('document_type')})")
                else:
                    st.success("All applicable mandatory requirements are satisfied!")
