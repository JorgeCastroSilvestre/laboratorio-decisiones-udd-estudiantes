from __future__ import annotations

import hmac
import os

import streamlit as st


def _access_config() -> tuple[str, set[str]]:
    password = os.getenv("PORTAL_STUDENT_PASSWORD", "").strip()
    email_text = os.getenv("PORTAL_ALLOWED_EMAILS", "")
    if password and email_text:
        return password, {item.strip().casefold() for item in email_text.split(",") if item.strip()}

    try:
        access = st.secrets.get("access", {})
    except (FileNotFoundError, OSError):
        access = {}
    password = str(access.get("student_password", "")).strip()
    emails = {str(item).strip().casefold() for item in access.get("allowed_emails", []) if str(item).strip()}
    return password, emails


def require_student_access() -> None:
    if os.getenv("PORTAL_PREVIEW_MODE", "").strip() == "1":
        return

    if st.session_state.get("student_authenticated") is True:
        with st.sidebar:
            st.caption("Sesión de estudiante activa")
            if st.button("Cerrar sesión", width="stretch"):
                st.session_state.pop("student_authenticated", None)
                st.session_state.pop("student_email", None)
                st.rerun()
        return

    expected_password, allowed_emails = _access_config()
    if not expected_password or not allowed_emails:
        st.error("El acceso estudiantil todavía no ha sido configurado por el docente.")
        st.stop()

    st.markdown("## Acceso al Portal de Estudiantes")
    st.caption("Ingrese con su correo UDD y la clave entregada por el docente.")
    with st.form("student_login"):
        email = st.text_input("Correo UDD", placeholder="correo institucional").strip().casefold()
        password = st.text_input("Clave de acceso", type="password")
        submitted = st.form_submit_button("Ingresar", type="primary")
    if submitted:
        if email in allowed_emails and hmac.compare_digest(password, expected_password):
            st.session_state.student_authenticated = True
            st.session_state.student_email = email
            st.rerun()
        else:
            st.error("Correo o clave incorrectos.")
    st.stop()
