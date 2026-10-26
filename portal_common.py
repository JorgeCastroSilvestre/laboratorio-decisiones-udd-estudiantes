from __future__ import annotations

import json
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parent
PUBLICATION_PATH = ROOT / "data" / "publication.json"
VISIBLE_ACTIVITY_NUMBERS = (1, 2, 3, 5)

INDICATOR_LABELS = {
    "findings": "Hallazgos",
    "evidence_items": "Evidencias",
    "decisions": "Decisiones",
}

AUDIENCE_LABELS = {
    "comite_directivo": "Comité directivo",
    "trabajadores": "Trabajadores",
    "operaciones": "Operaciones",
    "seguridad_gobernanza": "Seguridad y gobernanza de IA",
}


def load_publication() -> dict:
    try:
        data = json.loads(PUBLICATION_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_publication()
    if data.get("schema_version") != "1.0" or len(data.get("activities", [])) != 5:
        return empty_publication()
    return data


def empty_publication() -> dict:
    return {
        "schema_version": "1.0",
        "publication": {"id": None, "version": 0, "status": "empty", "prepared_at": None, "published_at": None},
        "laboratory": {
            "title": "Laboratorio de Decisiones con IA",
            "subtitle": "Diplomado UDD | Exploración de evidencia, análisis y toma de decisiones",
        },
        "activities": [
            {"activity_number": number, "name": f"Actividad Práctica {number}", "description": None, "objective": None, "results": []}
            for number in range(1, 6)
        ],
    }


def formatted_date(value: str | None) -> str:
    if not value:
        return "Sin actualizar"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d-%m-%Y")
    except ValueError:
        return "Fecha no disponible"


def hero(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'<header class="portal-hero"><small>{escape(kicker)}</small><h1>{escape(title)}</h1><p>{escape(subtitle)}</p></header>',
        unsafe_allow_html=True,
    )


def activity_by_number(data: dict, number: int) -> dict:
    return next((item for item in data["activities"] if item["activity_number"] == number), empty_publication()["activities"][number - 1])


def _activity_two_card(payload: dict) -> None:
    audience = AUDIENCE_LABELS.get(payload.get("audience_family") or payload.get("audience"), payload.get("audience", "No informada"))
    alternative = payload.get("alternative", "No informada")
    top = st.columns(2)
    top[0].metric("Audiencia", audience)
    top[1].metric("Alternativa comunicada", alternative)

    st.markdown("#### Mensaje ejecutivo")
    st.info(payload.get("central_message") or "Sin mensaje registrado")

    for index in (1, 2):
        finding = payload.get(f"finding_{index}")
        references = payload.get(f"references_{index}") or []
        if finding:
            st.markdown(f"**Hallazgo {index}**")
            st.write(finding)
            if references:
                st.caption("Evidencia vinculada: " + " · ".join(str(item) for item in references))

    details = [
        ("Matiz", payload.get("nuance")),
        ("Incertidumbre", payload.get("uncertainty")),
        ("Acción propuesta", payload.get("action")),
        ("Adaptación a la audiencia", payload.get("audience_adaptation")),
        ("Corrección humana", payload.get("human_correction")),
    ]
    st.markdown("#### Criterio y acción")
    for label, value in details:
        if value:
            st.markdown(f"**{label}.** {value}")


def _render_activity_data(number: int, payload: dict) -> None:
    if number == 2:
        _activity_two_card(payload)
        return
    st.subheader("Ficha de la actividad")
    st.json(payload, expanded=False)


def render_activity_payload(data: dict, number: int, *, show_version: bool = True) -> None:
    activity = activity_by_number(data, number)
    hero(f"Actividad {number:02d} · Resultados publicados", activity["name"], activity.get("objective") or "Exploración de evidencia y toma de decisiones.")
    results = activity.get("results", [])
    if not results:
        st.info("Esta actividad aún no tiene resultados publicados.")
        st.caption("La información aparecerá después de la revisión y publicación docente.")
        return

    group_options = [item["group"] for item in results]
    selected = st.multiselect("Grupos o casos", group_options, default=group_options)
    visible = [item for item in results if item["group"] in selected]
    indicators = pd.DataFrame([{"Grupo": item["group"], **item.get("indicators", {})} for item in visible])
    if not indicators.empty and len(indicators.columns) > 1:
        columns = st.columns(min(3, len(indicators.columns) - 1))
        for column, key in zip(columns, [key for key in indicators.columns if key != "Grupo"]):
            column.metric(INDICATOR_LABELS.get(key, key.replace("_", " ").title()), int(indicators[key].sum()))
        long = indicators.melt(id_vars="Grupo", var_name="Indicador", value_name="Cantidad")
        long["Indicador"] = long["Indicador"].map(lambda value: INDICATOR_LABELS.get(value, value.replace("_", " ").title()))
        figure = px.bar(long, x="Grupo", y="Cantidad", color="Indicador", barmode="group", title="Indicadores autorizados por grupo", color_discrete_sequence=["#005293", "#008dd2", "#f29400"])
        figure.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#243746")
        st.plotly_chart(figure, use_container_width=True)

    for result in visible:
        with st.expander(result["group"], expanded=len(visible) == 1):
            if result.get("activity_data"):
                _render_activity_data(number, result["activity_data"])
            if result.get("findings"):
                st.subheader("Hallazgos principales")
                for item in result["findings"]:
                    st.markdown(f"**{item.get('description', 'Hallazgo')}**")
                    if item.get("interpretation"):
                        st.write(item["interpretation"])
                    if item.get("limitations"):
                        st.caption(f"Límite: {item['limitations']}")
            if result.get("evidence"):
                st.subheader("Evidencia autorizada")
                st.dataframe(pd.DataFrame(result["evidence"]), hide_index=True, width="stretch")
            if result.get("decisions"):
                st.subheader("Decisiones y conclusiones")
                for decision in result["decisions"]:
                    st.markdown(f"**{decision.get('recommendation', 'Decisión')}**")
                    if decision.get("justification"):
                        st.write(decision["justification"])
                    if decision.get("risks"):
                        st.caption(f"Riesgos o matices: {decision['risks']}")
            if result.get("teacher_feedback"):
                st.subheader("Retroalimentación docente")
                st.info(result["teacher_feedback"])

    if show_version:
        st.caption(f"Versión pública {data['publication'].get('version', 0)} · Actualizada: {formatted_date(data['publication'].get('published_at'))}")


def render_activity(number: int) -> None:
    render_activity_payload(load_publication(), number)
