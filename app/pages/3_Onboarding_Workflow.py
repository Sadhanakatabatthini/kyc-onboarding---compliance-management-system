import sys
import os

app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_dir = os.path.abspath(os.path.join(app_dir, ".."))
for p in [app_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import streamlit as st
try:
    from app.components.helpers import render_role_selector, api_get, api_post
except ImportError:
    from components.helpers import render_role_selector, api_get, api_post

st.set_page_config(page_title="Onboarding Workflow | KYC Compliance", page_icon="📝", layout="wide")
render_role_selector()

st.title("📝 KYC Onboarding Workflow & Decision Engine")

role = st.session_state.get("current_role", "Operations Analyst")

tab_new, tab_eval = st.tabs(["➕ Create Customer Record", "⚖️ Onboarding Decision Evaluation"])

with tab_new:
    st.subheader("Register New Customer Applicant")
    if role not in ["Operations Analyst", "System Administrator"]:
        st.warning(f"Role '{role}' does not have permission to register new onboarding customers.")
    else:
        with st.form("new_customer_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Legal Full Name / Corporate Title:", placeholder="e.g. Johnathan Vance or Global Logix Corp")
            ctype = c2.selectbox("Customer Classification:", ["Individual Account", "Corporate Entity"])
            country = c1.selectbox("Country of Origin / Registration:", ["US", "GB", "DE", "SG", "CH", "FR", "NL", "AE", "HK", "JP"])
            channel = c2.selectbox("Acquisition Channel:", ["DIGITAL_PORTAL", "BRANCH", "RELATIONSHIP_MANAGER"])
            submitted = st.form_submit_button("Initiate Onboarding")

            if submitted:
                if not name.strip():
                    st.error("Legal name is required.")
                else:
                    payload = {
                        "legal_name": name.strip(),
                        "customer_type_id": 2 if "Corporate" in ctype else 1,
                        "country_code": country,
                        "onboarding_channel": channel
                    }
                    res, code = api_post("customers", payload)
                    if code == 201:
                        st.success(f"Customer successfully initiated! Assigned ID: `{res.get('customer_id')}`")
                    else:
                        st.error(f"Error: {res.get('error', 'Could not create customer')}")

with tab_eval:
    st.subheader("Evaluate Customer Decision (Gated Workflow)")
    cid_input = st.text_input("Enter Customer ID to evaluate:", placeholder="e.g. CUS-000001")
    if cid_input:
        profile = api_get(f"customers/{cid_input.strip()}")
        if not profile or "error" in profile:
            st.error("Customer not found.")
        else:
            cust = profile.get("customer", {})
            pct = profile.get("completeness_percentage", 0)
            status = cust.get("lifecycle_status")

            st.info(f"Customer: **{cust.get('legal_name')}** | Current Status: `{status}` | Completeness: `{pct}%`")

            st.markdown("#### Transition Actions")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("Mark UNDER_REVIEW", use_container_width=True):
                    res, code = api_post(f"customers/{cust['customer_id']}/decision", {"target_status": "UNDER_REVIEW", "reason": "Moving to formal compliance review"})
                    if code == 200:
                        st.success("Status transitioned to UNDER_REVIEW")
                        st.rerun()
                    else:
                        st.error(res.get("error"))

            with c2:
                if st.button("Approve KYC (Gated)", type="primary", use_container_width=True):
                    res, code = api_post(f"customers/{cust['customer_id']}/decision", {"target_status": "APPROVED", "reason": "Mandatory evidence verified"})
                    if code == 200:
                        st.success("Customer APPROVED successfully!")
                        st.rerun()
                    else:
                        st.error(f"Approval Blocked: {res.get('error')}")
                        for r in res.get("reasons", []):
                            st.warning(f"• {r}")

            with c3:
                reject_reason = st.text_input("Rejection Reason:", key="rej_input")
                if st.button("Reject KYC", type="secondary", use_container_width=True):
                    if not reject_reason.strip():
                        st.error("Rejection reason is mandatory.")
                    else:
                        res, code = api_post(f"customers/{cust['customer_id']}/decision", {"target_status": "REJECTED", "reason": reject_reason})
                        if code == 200:
                            st.warning("Customer REJECTED.")
                            st.rerun()
                        else:
                            st.error(res.get("error"))
