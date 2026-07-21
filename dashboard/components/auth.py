from __future__ import annotations

import os

import streamlit as st

from components.db import env_bool


SESSION_KEY = "bike_store_dashboard_authenticated"


def auth_enabled() -> bool:
    return env_bool("DASHBOARD_AUTH_ENABLED", default=False)


def _expected_credentials() -> tuple[str, str]:
    return (
        os.getenv("DASHBOARD_DEMO_USER", "").strip(),
        os.getenv("DASHBOARD_DEMO_PASSWORD", "").strip(),
    )


def require_authentication() -> None:
    if not auth_enabled():
        st.session_state[SESSION_KEY] = True
        return

    if st.session_state.get(SESSION_KEY):
        return

    st.title("Bike Store Analytics")
    st.subheader("Dang nhap demo")
    expected_user, expected_password = _expected_credentials()
    with st.form("dashboard_login"):
        username = st.text_input("User")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Dang nhap")

    if submitted:
        if not expected_user or not expected_password:
            st.error("Thieu DASHBOARD_DEMO_USER hoac DASHBOARD_DEMO_PASSWORD trong .env.")
        elif username == expected_user and password == expected_password:
            st.session_state[SESSION_KEY] = True
            st.rerun()
        else:
            st.error("Thong tin dang nhap khong dung.")

    st.stop()


def render_account_controls() -> None:
    if not auth_enabled():
        st.caption("Auth: off")
        return
    user = os.getenv("DASHBOARD_DEMO_USER", "").strip() or "demo"
    st.caption(f"User: {user}")
    if st.button("Dang xuat", width="stretch"):
        st.session_state[SESSION_KEY] = False
        st.rerun()
