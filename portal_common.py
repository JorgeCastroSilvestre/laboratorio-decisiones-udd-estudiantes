from __future__ import annotations

import json
import re
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
PUBLICATION_PATH = ROOT / "data" / "publication.json"
VISIBLE_ACTIVITY_NUMBERS = (1, 2, 3, 4, 5)

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
    "seguridad_gobernanza_ia": "Seguridad y gobernanza de IA",
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


def student_welcome() -> None:
    name = st.session_state.get("student_name")
    if name:
        st.caption(f"Sesión de estudiante · {name}")


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


def _activity_two_gallery() -> None:
    """Show only the submitted infographics as an expandable photo gallery."""
    assets = ROOT / "assets" / "activity_02"
    available = []
    for path in assets.glob("grupo_*_pagina_2.png"):
        match = re.fullmatch(r"grupo_(\d+)_pagina_2\.png", path.name)
        if not match:
            continue
        group_number = int(match.group(1))
        available.append({"label": f"Grupo {group_number}", "path": path, "group": group_number})
    available.sort(key=lambda item: item["group"])
    if not available:
        st.info("Las infografías aparecerán aquí después de ser publicadas por el docente.")
        return

    st.markdown("## Galería de infografías")
    st.caption("Selecciona una miniatura para verla en tamaño completo.")
    if "activity_02_selected_infographic" not in st.session_state:
        st.session_state.activity_02_selected_infographic = available[0]["label"]

    for start in range(0, len(available), 4):
        row = available[start : start + 4]
        columns = st.columns(4)
        for column, item in zip(columns, row):
            with column:
                st.image(str(item["path"]), caption=item["label"], width="stretch")
                if st.button(
                    "Ampliar",
                    key=f"open_{item['label']}",
                    width="stretch",
                    type="primary" if st.session_state.activity_02_selected_infographic == item["label"] else "secondary",
                ):
                    st.session_state.activity_02_selected_infographic = item["label"]

    selected = next(
        (item for item in available if item["label"] == st.session_state.activity_02_selected_infographic),
        available[0],
    )
    st.markdown(f"### Vista ampliada · {selected['label']}")
    st.image(str(selected["path"]), width="stretch")
    st.divider()


def _activity_two_analysis(results: list[dict]) -> None:
    """Student-safe version of the existing Activity 2 teaching dashboard."""
    rows = []
    for result in results:
        payload = result.get("activity_data") or {}
        if not payload:
            continue
        rows.append(
            {
                "grupo": result.get("group", "Grupo"),
                "audiencia": payload.get("audience") or payload.get("audience_family") or "No informada",
                "alternativa": payload.get("alternative") or "No informada",
                "mensaje_central": payload.get("central_message") or "",
                "referencias_1": payload.get("references_1") or [],
                "referencias_2": payload.get("references_2") or [],
                "matiz": payload.get("nuance") or "",
                "incertidumbre": payload.get("uncertainty") or "",
                "accion": payload.get("action") or "",
                "correccion_humana": payload.get("human_correction") or "",
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return

    st.markdown("## Análisis comparado de las decisiones")
    st.caption("Los gráficos reutilizan los campos autorizados del tablero docente y permiten comparar cómo cambia la comunicación según la audiencia.")
    teams = sorted(frame["grupo"].unique())
    audiences = sorted(frame["audiencia"].unique())
    alternatives = sorted(frame["alternativa"].unique())
    c1, c2, c3 = st.columns(3)
    selected_teams = c1.multiselect("Grupos", teams, default=teams, key="student_a2_groups")
    selected_audiences = c2.multiselect(
        "Audiencias",
        audiences,
        default=audiences,
        format_func=lambda value: AUDIENCE_LABELS.get(value, str(value).replace("_", " ").title()),
        key="student_a2_audiences",
    )
    selected_alternatives = c3.multiselect("Alternativas", alternatives, default=alternatives, key="student_a2_alternatives")
    filtered = frame[
        frame["grupo"].isin(selected_teams)
        & frame["audiencia"].isin(selected_audiences)
        & frame["alternativa"].isin(selected_alternatives)
    ].copy()
    if filtered.empty:
        st.info("No hay resultados para la combinación seleccionada.")
        return

    left, right = st.columns(2)
    decisions = filtered.groupby(["audiencia", "alternativa"]).size().reset_index(name="entregas")
    decisions["audiencia"] = decisions["audiencia"].map(lambda value: AUDIENCE_LABELS.get(value, str(value).replace("_", " ").title()))
    decision_figure = px.bar(
        decisions,
        x="audiencia",
        y="entregas",
        color="alternativa",
        barmode="group",
        text_auto=True,
        title="Decisiones por audiencia",
        labels={"audiencia": "Audiencia", "entregas": "Grupos", "alternativa": "Alternativa"},
        color_discrete_sequence=["#005293", "#008dd2", "#f29400"],
    )
    left.plotly_chart(decision_figure, use_container_width=True)

    reference_rows = []
    for _, row in filtered.iterrows():
        for field in ("referencias_1", "referencias_2"):
            reference_rows.extend({"grupo": row["grupo"], "codigo": str(code).strip()} for code in row[field] if str(code).strip())
    references = pd.DataFrame(reference_rows)
    if references.empty:
        right.info("No hay referencias disponibles para los filtros seleccionados.")
    else:
        reference_counts = references.groupby("codigo").size().reset_index(name="usos").sort_values("usos", ascending=False)
        reference_figure = px.bar(
            reference_counts.head(15),
            x="codigo",
            y="usos",
            text_auto=True,
            title="Referencias más utilizadas",
            labels={"codigo": "Referencia", "usos": "Usos"},
            color_discrete_sequence=["#008dd2"],
        )
        right.plotly_chart(reference_figure, use_container_width=True)

    criteria = {
        "Mensaje central": filtered["mensaje_central"].str.strip().ne(""),
        "Referencias": filtered.apply(lambda row: bool(row["referencias_1"] and row["referencias_2"]), axis=1),
        "Matiz": filtered["matiz"].str.strip().ne(""),
        "Incertidumbre": filtered["incertidumbre"].str.strip().ne(""),
        "Acción": filtered["accion"].str.strip().ne(""),
        "Corrección humana": filtered["correccion_humana"].str.strip().ne(""),
    }
    values = [[1 if criteria[name].loc[index] else 0 for name in criteria] for index in filtered.index]
    traceability = go.Figure(
        go.Heatmap(
            z=values,
            x=list(criteria),
            y=filtered["grupo"],
            zmin=0,
            zmax=1,
            colorscale=[[0, "#E7EEF3"], [1, "#008DD2"]],
            showscale=False,
            text=[["Presente" if cell else "Pendiente" for cell in row] for row in values],
            texttemplate="%{text}",
            hovertemplate="%{y}<br>%{x}: %{text}<extra></extra>",
        )
    )
    traceability.update_layout(title="Trazabilidad del mensaje a la acción", xaxis_title="", yaxis_title="")
    st.plotly_chart(traceability, use_container_width=True)

    st.markdown("### Mensajes, acciones y límites")
    table = filtered[["grupo", "audiencia", "alternativa", "mensaje_central", "accion", "matiz", "incertidumbre", "correccion_humana"]].copy()
    table["audiencia"] = table["audiencia"].map(lambda value: AUDIENCE_LABELS.get(value, str(value).replace("_", " ").title()))
    table.columns = ["Grupo", "Audiencia", "Alternativa", "Mensaje central", "Acción", "Matiz", "Incertidumbre", "Corrección humana"]
    st.dataframe(table, hide_index=True, width="stretch")


def _activity_three_carousel() -> None:
    """Show the two submitted pages for each published group before the analysis."""
    assets = ROOT / "assets" / "activity_03"
    groups: dict[int, list[Path]] = {}
    for path in assets.glob("grupo_*_pagina_*.png"):
        match = re.fullmatch(r"grupo_(\d+)_pagina_(1|2)\.png", path.name)
        if match:
            groups.setdefault(int(match.group(1)), []).append(path)
    complete = {number: sorted(paths) for number, paths in groups.items() if len(paths) >= 2}
    if not complete:
        return

    numbers = sorted(complete)
    labels = [f"Grupo {number}" for number in numbers]
    state_key = "activity_03_carousel_group"
    if st.session_state.get(state_key) not in labels:
        st.session_state[state_key] = labels[0]

    def move(step: int) -> None:
        current = labels.index(st.session_state.get(state_key, labels[0]))
        st.session_state[state_key] = labels[(current + step) % len(labels)]

    st.markdown("## Carrusel de fichas y evidencia visual")
    st.caption("Recorre los grupos y compara la ficha ejecutiva con las dos fotografías seleccionadas por cada equipo.")
    controls = st.columns([1, 4, 1])
    controls[0].button("Anterior", key="activity_03_previous", on_click=move, args=(-1,), width="stretch")
    selected = controls[1].selectbox("Grupo", labels, key=state_key, label_visibility="collapsed")
    controls[2].button("Siguiente", key="activity_03_next", on_click=move, args=(1,), width="stretch")
    selected_number = int(selected.split()[-1])
    pages = complete[selected_number]
    page_columns = st.columns(2)
    for index, (column, path) in enumerate(zip(page_columns, pages[:2]), start=1):
        with column:
            st.image(str(path), caption=f"{selected} · Página {index} de 2", width="stretch")
    st.divider()


def _load_activity_four_analysis() -> dict:
    path = ROOT / "assets" / "activity_04" / "analysis.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"groups": []}


def _activity_four_dashboard(results: list[dict]) -> bool:
    analysis = _load_activity_four_analysis()
    published_groups = {item.get("group") for item in results}
    groups = [item for item in analysis.get("groups", []) if item.get("group") in published_groups]
    if not groups:
        return False

    options = [item["group"] for item in groups]
    selected_group = st.selectbox("Trabajo publicado", options, key="activity_04_group")
    selected = next(item for item in groups if item["group"] == selected_group)
    periods = pd.DataFrame(selected["periods"]).sort_values("period")
    latest = periods.iloc[-1]
    previous = periods.iloc[-2] if len(periods) > 1 else latest

    st.markdown(f"## {selected['pharmacy']} · lectura ejecutiva")
    st.caption(f"{selected_group} · Alternativa final: {selected['alternative']}")
    metrics = st.columns(4)
    metrics[0].metric("NPS 2020", f"{float(previous['nps']):.1f}")
    metrics[1].metric("NPS 2021", f"{float(latest['nps']):.1f}", f"{float(latest['nps'] - previous['nps']):+.1f}")
    metrics[2].metric("Respuestas reales", int(periods["valid"].sum()))
    metrics[3].metric("Alternativa", selected["alternative"].split("·", 1)[0].strip())

    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=float(latest["nps"]),
            number={"suffix": " pts", "font": {"size": 46, "color": "#081C2B"}},
            delta={"reference": float(previous["nps"]), "valueformat": ".1f"},
            title={"text": f"Tacómetro NPS · {int(latest['period'])}", "font": {"size": 22}},
            gauge={
                "axis": {"range": [-100, 100], "tickwidth": 1, "tickcolor": "#667987"},
                "bar": {"color": "#005293", "thickness": 0.28},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [-100, 0], "color": "#F7D6D8"},
                    {"range": [0, 30], "color": "#FFE6B8"},
                    {"range": [30, 70], "color": "#CDEFFC"},
                    {"range": [70, 100], "color": "#CDEEDC"},
                ],
                "threshold": {"line": {"color": "#F29400", "width": 5}, "thickness": 0.8, "value": float(latest["nps"])},
            },
        )
    )
    gauge.update_layout(height=390, margin=dict(l=30, r=30, t=75, b=20), paper_bgcolor="rgba(0,0,0,0)")

    sentiment = pd.DataFrame(selected["sentiment"])
    sentiment_figure = px.bar(
        sentiment,
        x="period",
        y="comments",
        color="sentiment",
        barmode="stack",
        text_auto=True,
        title="Sentimiento textual por período",
        labels={"period": "Período", "comments": "Comentarios", "sentiment": "Sentimiento"},
        color_discrete_map={"Positivo": "#00A99D", "Mixto / neutro": "#A9BBC7", "Negativo": "#E45B64"},
    )
    sentiment_figure.update_layout(height=390, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    charts = st.columns([1, 1.15])
    charts[0].plotly_chart(gauge, use_container_width=True)
    charts[1].plotly_chart(sentiment_figure, use_container_width=True)

    topics = pd.DataFrame(selected["topics"])
    topic_figure = px.bar(
        topics,
        x="topic",
        y="mentions",
        color="period",
        barmode="group",
        text_auto=True,
        title="Temas mencionados en los comentarios reales",
        labels={"topic": "Tema", "mentions": "Menciones", "period": "Período"},
        color_discrete_sequence=["#005293", "#F29400"],
    )
    topic_figure.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(topic_figure, use_container_width=True)

    st.markdown("### De la evidencia a la decisión")
    st.info(f"**Problema identificado.** {selected['problem']}")
    st.success(f"**Recomendación.** {selected['recommendation']}")
    st.warning(f"**Contraste y límite.** {selected['contrast']}")
    st.caption(selected["evidence_note"])
    st.caption(analysis.get("methodology", ""))
    return True


def _render_activity_data(number: int, payload: dict) -> None:
    if number == 2:
        _activity_two_card(payload)
        return
    st.subheader("Ficha de la actividad")
    st.json(payload, expanded=False)


def render_activity_payload(data: dict, number: int, *, show_version: bool = True) -> None:
    activity = activity_by_number(data, number)
    results = sorted(activity.get("results", []), key=lambda item: item.get("group", ""))
    student_welcome()
    hero(f"Actividad {number:02d} · Resultados publicados", activity["name"], activity.get("objective") or "Exploración de evidencia y toma de decisiones.")
    if number == 2:
        _activity_two_gallery()
        _activity_two_analysis(results)
        if show_version:
            st.caption(f"Versión pública {data['publication'].get('version', 0)} · Actualizada: {formatted_date(data['publication'].get('published_at'))}")
        return
    if number == 3:
        _activity_three_carousel()
    if number == 4 and _activity_four_dashboard(results):
        if show_version:
            st.caption(f"Versión pública {data['publication'].get('version', 0)} · Actualizada: {formatted_date(data['publication'].get('published_at'))}")
        return
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
