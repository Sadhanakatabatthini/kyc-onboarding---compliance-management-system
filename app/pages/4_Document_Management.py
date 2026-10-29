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

st.set_page_config(page_title="Document Management | KYC Compliance", page_icon="📄", layout="wide")
render_role_selector()

st.title("📄 Document Evidence Management & Verification")

c1, c2 = st.columns(2)
status_filter = c1.selectbox("Filter Document Status:", ["ALL", "VALID", "SUBMITTED", "EXPIRED", "INVALID"])
doc_type_filter = c2.selectbox("Filter Document Type:", ["ALL", "PASSPORT", "PROOF_OF_ADDRESS", "CERT_INCORPORATION", "ARTICLES_OF_ASSOC", "BENEFICIAL_OWNERSHIP_DECLARATION"])

params = {}
if status_filter != "ALL":
    params["status"] = status_filter
if doc_type_filter != "ALL":
    params["document_type"] = doc_type_filter

resp = api_get("documents", params=params)
if not resp:
    st.info("Loading documents...")
    st.stop()

docs = resp.get("items", [])
st.caption(f"Total documents: {len(docs)}")

if docs:
    df = pd.DataFrame(docs)
    st.dataframe(df[["document_id", "customer_id", "document_type", "issue_date", "expiry_date", "document_status", "document_reference"]], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔍 Document Verification Action")
    sel_doc_id = st.selectbox("Select Document ID to verify:", [d["document_id"] for d in docs])

    if sel_doc_id:
        doc = next(d for d in docs if d["document_id"] == sel_doc_id)
        st.write(f"Evaluating: **{doc['document_id']}** for Customer: `{doc['customer_id']}` | Reference: `{doc['document_reference']}`")
        st.write(f"Issue Date: `{doc['issue_date']}` | Expiry Date: `{doc.get('expiry_date', 'Non-expiring')}` | Status: `{doc['document_status']}`")

        with st.form("verify_form"):
            v_outcome = st.selectbox("Verification Outcome:", ["PASSED", "FAILED", "PENDING_MORE_INFO"])
            v_method = st.selectbox("Verification Method:", ["MANUAL_ANALYST", "AUTOMATED_OCR", "THIRD_PARTY_BUREAU"])
            v_reason = st.text_input("Reason Code:", value="SECURITY_FEATURES_CONFIRMED")
            v_comments = st.text_area("Analyst Inspection Notes:", value="Document inspected, security hologram and biometric MRZ lines verified.")
            submit_ver = st.form_submit_button("Record Verification", type="primary")

            if submit_ver:
                payload = {
                    "verification_status": v_outcome,
                    "verification_method": v_method,
                    "reason_code": v_reason,
                    "comments": v_comments
                }
                res, code = api_post(f"documents/{sel_doc_id}/verify", payload)
                if code == 200:
                    st.success(f"Verification successfully recorded for {sel_doc_id}! New status: `{res['document']['document_status']}`")
                    st.rerun()
                else:
                    st.error(res.get("error", "Failed to record verification"))
