from __future__ import annotations

from html import escape

import streamlit as st

from portal_common import VISIBLE_ACTIVITY_NUMBERS, formatted_date, hero, load_publication


data = load_publication()
visible_activities = [activity for activity in data["activities"] if activity["activity_number"] in VISIBLE_ACTIVITY_NUMBERS]
hero(
    "Diplomado UDD · Portal de estudiantes",
    "Laboratorio de Decisiones con IA",
    "Exploración de evidencia, análisis y toma de decisiones. Aquí encontrarás exclusivamente resultados revisados y autorizados por el equipo docente.",
)
published = sum(len(activity.get("results", [])) for activity in visible_activities)
modules = sum(bool(activity.get("results")) for activity in visible_activities)
left, middle, right = st.columns(3)
left.metric("Resultados publicados", published)
middle.metric("Actividades con resultados", f"{modules} / {len(VISIBLE_ACTIVITY_NUMBERS)}")
right.metric("Última actualización", formatted_date(data["publication"].get("published_at")))

st.subheader("Explora las actividades")
columns = st.columns(3)
for index, activity in enumerate(visible_activities):
    number = activity["activity_number"]
    count = len(activity.get("results", []))
    status = f"{count} resultado{'s' if count != 1 else ''}" if count else "Sin publicaciones"
    with columns[index % 3]:
        st.markdown(
            f'<div class="activity-card"><small>ACTIVIDAD {number:02d}</small><h3>{escape(activity["name"])}</h3><p>{escape(activity.get("objective") or "Módulo preparado para futuras publicaciones.")}</p><span class="status">{escape(status)}</span></div>',
            unsafe_allow_html=True,
        )
        st.page_link(f"pages/actividad_{number:02d}.py", label="Ver actividad", width="stretch")

st.caption("Portal de solo lectura. Los datos internos, entregas originales e información personal no forman parte de esta publicación.")
