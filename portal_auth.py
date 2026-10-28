from __future__ import annotations

import hmac
import json
import os

import streamlit as st


def _access_config() -> tuple[str, set[str], dict[str, str]]:
    password = os.getenv("PORTAL_STUDENT_PASSWORD", "").strip()
    email_text = os.getenv("PORTAL_ALLOWED_EMAILS", "")
    names_text = os.getenv("PORTAL_STUDENT_NAMES", "").strip()
    if password and email_text:
        try:
            names = json.loads(names_text) if names_text else {}
        except json.JSONDecodeError:
            names = {}
        return (
            password,
            {item.strip().casefold() for item in email_text.split(",") if item.strip()},
            {str(email).strip().casefold(): str(name).strip() for email, name in names.items()},
        )

    try:
        access = st.secrets.get("access", {})
    except (FileNotFoundError, OSError):
        access = {}
    password = str(access.get("student_password", "")).strip()
    emails = {str(item).strip().casefold() for item in access.get("allowed_emails", []) if str(item).strip()}
    raw_names = access.get("student_names", {})
    names = {str(email).strip().casefold(): str(name).strip() for email, name in dict(raw_names).items()}
    return password, emails, names


def _fallback_name(email: str) -> str:
    local = email.split("@", 1)[0]
    return " ".join(part.capitalize() for part in local.replace("_", ".").split(".") if part)


def require_student_access() -> None:
    if os.getenv("PORTAL_PREVIEW_MODE", "").strip() == "1":
        st.session_state.setdefault("student_name", "Vista docente")
        return

    if st.session_state.get("student_authenticated") is True:
        _, _, names = _access_config()
        email = str(st.session_state.get("student_email", ""))
        st.session_state.setdefault("student_name", names.get(email, _fallback_name(email)))
        with st.sidebar:
            st.markdown(f"**{st.session_state.student_name}**")
            st.caption(f"Estudiante · {email}")
            if st.button("Cerrar sesión", width="stretch"):
                st.session_state.pop("student_authenticated", None)
                st.session_state.pop("student_email", None)
                st.session_state.pop("student_name", None)
                st.rerun()
        return

    expected_password, allowed_emails, student_names = _access_config()
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
            st.session_state.student_name = student_names.get(email, _fallback_name(email))
            st.rerun()
        else:
            st.error("Correo o clave incorrectos.")
    st.stop()
