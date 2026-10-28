from __future__ import annotations

from html import escape

import streamlit as st

from portal_common import VISIBLE_ACTIVITY_NUMBERS, formatted_date, hero, load_publication


data = load_publication()
visible_activities = [activity for activity in data["activities"] if activity["activity_number"] in VISIBLE_ACTIVITY_NUMBERS]
student_name = st.session_state.get("student_name")
if student_name:
    st.caption(f"Sesión de estudiante · {student_name}")
hero(
    "Diplomado UDD · Portal de estudiantes",
    "Laboratorio de Decisiones con IA",
    "Exploración de evidencia, análisis y toma de decisiones. Aquí encontrarás exclusivamente resultados revisados y autorizados por el equipo docente.",
)
published = sum(len(activity.get("results", [])) for activity in visible_activities)
left, middle, right, update = st.columns(4)
left.metric("Actividades disponibles", len(VISIBLE_ACTIVITY_NUMBERS))
middle.metric("Resultados publicados", published)
right.metric("Laboratorios interactivos", 1)
update.metric("Última actualización", formatted_date(data["publication"].get("published_at")))

st.subheader("Explora las actividades")
columns = st.columns(2)
for index, activity in enumerate(visible_activities):
    number = activity["activity_number"]
    count = len(activity.get("results", []))
    interactive = number == 5
    display_name = "Decisiones estratégicas bajo incertidumbre" if interactive else activity["name"]
    display_objective = (
        "Afinar una decisión sobre Farmacia Cruz Blanca al modificar prioridades, restricciones y nueva evidencia."
        if interactive
        else (activity.get("objective") or "Módulo preparado para futuras publicaciones.")
    )
    status = "Simulador disponible" if interactive else (f"{count} resultado{'s' if count != 1 else ''}" if count else "Sin publicaciones")
    with columns[index % 2]:
        st.markdown(
            f'<div class="activity-card"><small>ACTIVIDAD {number:02d}</small><h3>{escape(display_name)}</h3><p>{escape(display_objective)}</p><span class="status">{escape(status)}</span></div>',
            unsafe_allow_html=True,
        )
        st.page_link(
            "pages/actividad_05_v4.py" if number == 5 else f"pages/actividad_{number:02d}.py",
            label="Abrir simulador" if interactive else "Ver actividad",
            width="stretch",
        )

st.caption("Las actividades 1–4 son de consulta. La Actividad 5 permite simular y descargar una ficha; no expone datos internos, entregas originales ni información personal.")
