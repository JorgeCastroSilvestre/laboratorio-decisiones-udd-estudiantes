from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from executive_pdf import build_decision_pdf
from pharmacy_05_simulator import (
    ALTERNATIVES,
    CRITERIA,
    EVIDENCE,
    LABELS,
    SCENARIOS,
    decision_explanation,
    effective_budget,
    evaluate,
    normalize_weights,
    recommendation,
    sensitivity,
)
from portal_common import hero


hero(
    "Actividad 05 · Decisiones estratégicas bajo incertidumbre",
    "Afinar una decisión con nueva evidencia",
    "Retoma el caso Farmacia Cruz Blanca de la Actividad 04, modifica prioridades y restricciones, compara estrategias y argumenta una decisión revisable.",
)

st.caption("40 minutos · Flujo oficial: Simular → Guardar ANTES → incorporar evidencia → Guardar DESPUÉS → argumentar → descargar ficha")
team = st.selectbox("Equipo", ["Grupo 1", "Grupo 2", "Grupo 3", "Grupo 4"], key="a5_team")
st.info("La evidencia es real y anonimizada; los nombres de farmacia son alias docentes. Los puntajes 1–5 del simulador son supuestos didácticos y no predicciones.")


st.markdown("## 1. Evidencia heredada")
st.write("La Actividad 05 no parte de cero: recupera los agregados verificados y la muestra cualitativa revisada en la Actividad 04.")
aggregates = pd.DataFrame(EVIDENCE["aggregates"])
metric_cols = st.columns(4)
metric_cols[0].metric("NPS 2020", "11,9")
metric_cols[1].metric("NPS 2021", "13,0", "+1,1")
metric_cols[2].metric("Respuestas válidas", int(aggregates["valid"].sum()))
metric_cols[3].metric("Comentarios Cruz Blanca", EVIDENCE["qualitative_comments"])

topics = pd.DataFrame(EVIDENCE["topics"])
evidence_chart = px.bar(
    topics,
    x="topic",
    y="mentions",
    color="period",
    barmode="group",
    text_auto=True,
    labels={"topic": "Tema", "mentions": "Menciones", "period": "Periodo"},
    title="Temas detectados en la muestra cualitativa autorizada",
    color_discrete_sequence=["#005293", "#F29400"],
)
evidence_chart.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(evidence_chart, use_container_width=True)
st.caption("Una mención indica presencia del tema en un comentario; no equivale a prevalencia poblacional ni prueba causalidad.")
with st.expander("Trazabilidad y límites de las fuentes"):
    st.markdown(
        "- **Agregados verificados:** 2020 y 2021, Farmacia Cruz Blanca.\n"
        "- **Muestra cualitativa autorizada:** 28 comentarios Cruz Blanca dentro de la muestra didáctica de 111 comentarios.\n"
        f"- **Taxonomía de referencia:** {EVIDENCE['taxonomy_rows']:,} registros del archivo histórico utilizado para estructurar categorías; no se usa para calcular los NPS mostrados.\n"
        "- **Límite:** el simulador ayuda a comparar; no establece que una intervención causará el resultado esperado."
    )


st.markdown("## 2. Prioridades de gestión")
st.caption("Las prioridades se normalizan a 100 %. El presupuesto actúa como restricción y nunca como peso.")
defaults = {"productivity": 7, "wellbeing": 6, "collaboration": 5}
weights = {}
priority_cols = st.columns(3)
for index, key in enumerate(CRITERIA):
    weights[key] = priority_cols[index].slider(LABELS[key], 0, 10, defaults[key], key=f"a5v4_{key}")
budget = st.slider("Presupuesto disponible", 1, 5, 3, help="1 = muy restringido; 5 = holgado. El modelo excluye estrategias que exceden este nivel.", key="a5v4_budget")

with st.expander("Controles avanzados"):
    advanced = st.columns(3)
    risk = advanced[0].slider("Tolerancia al riesgo", 1, 5, 3, key="a5v4_risk")
    horizon = advanced[1].slider("Horizonte", 30, 90, 90, step=15, format="%d días", key="a5v4_horizon")
    restrictions = {
        "ninguna": "Sin restricción adicional",
        "equipo_comercial_saturado": "Equipo comercial saturado",
        "dependencia_proveedores": "Dependencia de proveedores",
        "capacidad_analitica_limitada": "Capacidad analítica limitada",
    }
    operational = advanced[2].selectbox("Restricción operativa", list(restrictions), format_func=lambda value: restrictions[value], key="a5v4_operational")

normalized = normalize_weights(weights)
weight_frame = pd.DataFrame({"Prioridad": [LABELS[key] for key in CRITERIA], "Porcentaje": [normalized[key] * 100 for key in CRITERIA]})
weight_chart = px.bar(weight_frame, x="Porcentaje", y="Prioridad", orientation="h", text_auto=".0f", color="Porcentaje", color_continuous_scale=["#CDEFFC", "#008DD2", "#005293"], range_x=[0, 100], title="Cómo queda distribuida la importancia")
weight_chart.update_layout(coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(weight_chart, use_container_width=True)


st.markdown("## 3. Comparación estratégica")
before = evaluate(weights, budget, risk, horizon, operational)
before_winner, _ = recommendation(before)
display_columns = {"alternative": "Estrategia", "name": "Decisión", "score": "Puntaje", "feasible": "Viable", "constraint": "Lectura de restricciones", "budget_required": "Presupuesto", "risk_level": "Riesgo", "days": "Días"}
st.dataframe(before.rename(columns=display_columns), hide_index=True, width="stretch", column_config={"Puntaje": st.column_config.NumberColumn(format="%.2f")})
before_chart = px.bar(before, x="alternative", y="score", color="feasible", text_auto=".2f", hover_name="name", range_y=[0, 5], labels={"alternative": "Estrategia", "score": "Puntaje", "feasible": "Viable"}, title="Resultado inicial: puntaje y viabilidad", color_discrete_map={True: "#008DD2", False: "#AAB8C2"})
before_chart.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(before_chart, use_container_width=True)
st.info(decision_explanation(before, weights, None))

if st.button("Guardar decisión ANTES", type="primary", use_container_width=True):
    st.session_state.a5v4_before = {"team": team, "winner": before_winner, "scores": before.to_dict("records"), "weights": dict(weights), "budget": budget, "risk": risk, "horizon": horizon, "operational": operational}
    st.toast("Decisión inicial registrada en esta sesión.")


st.markdown("## 4. Nueva evidencia")
scenario_labels = {"": "Selecciona una tarjeta"} | {key: value["title"] for key, value in SCENARIOS.items()}
scenario = st.selectbox("Tarjeta liberada por el docente", list(scenario_labels), format_func=lambda value: scenario_labels[value], key="a5v4_scenario")
selected_scenario = scenario or None
if selected_scenario:
    scenario_data = SCENARIOS[selected_scenario]
    st.warning(f"**{scenario_data['title']}.** {scenario_data['description']} {scenario_data['effect']}")
    if selected_scenario == "budget_reduced":
        st.caption(f"Presupuesto declarado: {budget} · Presupuesto efectivo bajo la nueva evidencia: {effective_budget(budget, selected_scenario)}")

after = evaluate(weights, budget, risk, horizon, operational, selected_scenario)
after_winner, _ = recommendation(after)
snapshot = st.session_state.get("a5v4_before")
if snapshot:
    comparison = pd.DataFrame(snapshot["scores"])[["alternative", "score"]].rename(columns={"score": "ANTES"}).merge(after[["alternative", "score"]].rename(columns={"score": "DESPUÉS"}), on="alternative").melt("alternative", var_name="Momento", value_name="Puntaje")
else:
    comparison = before[["alternative", "score"]].rename(columns={"score": "ANTES"}).merge(after[["alternative", "score"]].rename(columns={"score": "DESPUÉS"}), on="alternative").melt("alternative", var_name="Momento", value_name="Puntaje")
compare_chart = px.bar(comparison, x="alternative", y="Puntaje", color="Momento", barmode="group", text_auto=".2f", range_y=[0, 5], labels={"alternative": "Estrategia"}, title="Qué cambió entre la decisión inicial y la revisada", color_discrete_sequence=["#7895A6", "#F29400"])
compare_chart.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(compare_chart, use_container_width=True)
st.info(decision_explanation(after, weights, selected_scenario))

sens = sensitivity(weights, budget, risk, horizon, operational, selected_scenario)
winner_counts = sens.groupby("winner", as_index=False).size().rename(columns={"winner": "Estrategia", "size": "Variaciones"})
robust_chart = px.bar(winner_counts, x="Estrategia", y="Variaciones", color="Estrategia", text_auto=True, title="Robustez: estrategia ganadora al mover cada prioridad ±2", color_discrete_sequence=["#005293", "#008DD2", "#00A99D", "#F29400"])
robust_chart.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(robust_chart, use_container_width=True)
with st.expander("Ver detalle del análisis de sensibilidad"):
    detail = sens.rename(columns={"criterion": "Prioridad", "variation": "Variación", "winner": "Ganadora", "note": "Lectura"})
    st.dataframe(detail, hide_index=True, width="stretch")

if st.button("Guardar decisión DESPUÉS", disabled=not selected_scenario, use_container_width=True):
    st.session_state.a5v4_after = {"team": team, "winner": after_winner, "scores": after.to_dict("records"), "scenario": selected_scenario}
    st.toast("Decisión revisada registrada en esta sesión.")


st.markdown("## 5. Decisión y ficha ejecutiva")
before_saved = st.session_state.get("a5v4_before")
after_saved = st.session_state.get("a5v4_after")
status_cols = st.columns(2)
status_cols[0].metric("Decisión ANTES", before_saved.get("winner", "Pendiente") if before_saved else "Pendiente")
status_cols[1].metric("Decisión DESPUÉS", after_saved.get("winner", "Pendiente") if after_saved else "Pendiente")

default_code = after_saved.get("winner") if after_saved else after_winner
default_code = default_code or "D"
with st.form("a5v4_sheet"):
    chosen = st.selectbox("Estrategia recomendada", list(ALTERNATIVES), index=list(ALTERNATIVES).index(default_code), format_func=lambda code: f"{code} · {ALTERNATIVES[code]['name']}")
    evidence = st.text_area("Dos evidencias que respaldan la decisión")
    contrary = st.text_area("Evidencia o límite que la cuestiona")
    tradeoff = st.text_area("Principal trade-off")
    change = st.text_area("Qué cambió después de la nueva evidencia")
    condition = st.text_area("Condición para revisar o suspender")
    save_sheet = st.form_submit_button("Guardar ficha", type="primary", disabled=not (before_saved and after_saved))
if save_sheet:
    record = {"team": team, "strategy": f"{chosen} · {ALTERNATIVES[chosen]['name']}", "evidence": evidence, "contrary": contrary, "tradeoff": tradeoff, "change": change, "condition": condition}
    st.session_state.a5v4_sheet = record
    st.session_state.a5v4_pdf = build_decision_pdf(record)
    st.success("Ficha preparada. Revísala y descarga el PDF.")

if st.session_state.get("a5v4_pdf"):
    st.download_button("Descargar ficha PDF", st.session_state.a5v4_pdf, f"actividad_05_{team.lower().replace(' ', '_')}.pdf", "application/pdf", use_container_width=True)
else:
    st.caption("Para habilitar la ficha: guarda ANTES, selecciona nueva evidencia, guarda DESPUÉS y completa la argumentación.")

st.warning("Importante: el portal público mantiene los registros de la Actividad 05 durante la sesión abierta. No cierres la pestaña antes de descargar la ficha PDF.")
