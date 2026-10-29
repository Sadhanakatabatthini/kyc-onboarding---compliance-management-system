import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api/v1")

def api_get(endpoint: str, params: dict = None):
    try:
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        return None

def api_post(endpoint: str, payload: dict = None, headers: dict = None):
    try:
        url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
        default_headers = {
            "Content-Type": "application/json",
            "X-Actor-Id": st.session_state.get("current_user", "analyst_01"),
            "X-Actor-Role": st.session_state.get("current_role", "Operations Analyst")
        }
        if headers:
            default_headers.update(headers)
        resp = requests.post(url, json=payload, headers=default_headers, timeout=15)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def render_role_selector():
    with st.sidebar:
        st.markdown("### 👤 User Persona & Role")
        roles = [
            "Operations Analyst",
            "Risk / Compliance Reviewer",
            "System Administrator",
            "Customer / Account Holder"
        ]
        if "current_role" not in st.session_state:
            st.session_state.current_role = "Operations Analyst"
        
        selected_role = st.selectbox(
            "Current Role:",
            roles,
            index=roles.index(st.session_state.current_role),
            key="role_selector"
        )
        st.session_state.current_role = selected_role

        st.caption(f"Authenticated as: `{selected_role}`")
        st.markdown("---")
        st.markdown("**System Environment:** MySQL 8.0 & Flask REST")
