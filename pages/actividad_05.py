from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from activity_05_simulator import ALTERNATIVES, CRITERIA, LABELS, SCENARIOS, evaluate, normalize_weights, recommendation, sensitivity
from portal_common import activity_by_number, hero, load_publication


data = load_publication()
activity = activity_by_number(data, 5)
hero(
    "Actividad 05 · Laboratorio interactivo",
    activity["name"],
    activity.get("objective") or "Comparar alternativas, modificar supuestos y evaluar la robustez de una decisión.",
)

st.info(
    "Caso y cifras simuladas: organización chilena ficticia de servicios profesionales, "
    "180 personas y horizonte de 90 días. Los puntajes son supuestos didácticos, no datos observados."
)

st.markdown("### El desafío")
st.write(
    "La organización debe definir su política de trabajo para los próximos 90 días. "
    "Tu tarea no es aceptar automáticamente el puntaje mayor: debes reconocer qué preferencias, "
    "restricciones y evidencias hacen razonable una alternativa."
)
steps = st.columns(4)
for column, title, text in zip(
    steps,
    ["1 · Explorar", "2 · Comparar", "3 · Experimentar", "4 · Argumentar"],
    [
        "Comprende el caso, las alternativas y los supuestos.",
        "Mueve prioridades y observa qué políticas resultan viables.",
        "Incorpora nueva evidencia y prueba la sensibilidad.",
        "Explica la decisión, el trade-off y cuándo revisarla.",
    ],
):
    column.markdown(f"**{title}**")
    column.caption(text)

with st.expander("Alternativas y escala del modelo", expanded=False):
    alternatives_table = pd.DataFrame(
        [
            {
                "Código": code,
                "Política": values["name"],
                "Costo requerido": values["cost_level"],
                "Riesgo requerido": values["risk_level"],
                "Días": values["days"],
            }
            for code, values in ALTERNATIVES.items()
        ]
    )
    st.dataframe(alternatives_table, hide_index=True, width="stretch")
    st.caption("Escala 1–5: 1 representa un desempeño bajo y 5 uno alto. En costos y riesgo, un valor alto indica una valoración más favorable del criterio.")

st.markdown("### 1. Define tus prioridades")
st.caption("Las ponderaciones expresan preferencias; no son hechos objetivos. Se normalizan automáticamente para sumar 100%.")
default_weights = {
    "productivity": 7,
    "collaboration": 6,
    "wellbeing": 6,
    "costs": 4,
    "risk": 5,
    "continuity": 7,
}
weights: dict[str, int] = {}
weight_columns = st.columns(3)
for index, key in enumerate(CRITERIA):
    weights[key] = weight_columns[index % 3].slider(
        LABELS[key],
        0,
        10,
        default_weights[key],
        key=f"student_a5_weight_{key}",
    )

constraint_columns = st.columns(3)
budget = constraint_columns[0].slider(
    "Presupuesto disponible",
    1,
    5,
    3,
    help="1 = muy restringido · 5 = holgado",
    key="student_a5_budget",
)
risk_tolerance = constraint_columns[1].slider(
    "Tolerancia al riesgo",
    1,
    5,
    3,
    key="student_a5_risk",
)
horizon = constraint_columns[2].slider(
    "Horizonte de implementación",
    15,
    90,
    90,
    step=15,
    format="%d días",
    key="student_a5_horizon",
)

normalized = normalize_weights(weights)
weight_chart = pd.DataFrame(
    {"Criterio": [LABELS[key] for key in CRITERIA], "Peso": [normalized[key] * 100 for key in CRITERIA]}
)
weight_figure = px.bar(
    weight_chart,
    x="Peso",
    y="Criterio",
    orientation="h",
    color="Peso",
    color_continuous_scale=["#ccecf8", "#008dd2", "#005293"],
    range_x=[0, max(35, weight_chart["Peso"].max() + 5)],
    title="Prioridades normalizadas",
)
weight_figure.update_layout(coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(weight_figure, use_container_width=True)

st.markdown("### 2. Compara las políticas")
round_one = evaluate(weights, budget, risk_tolerance, horizon)
winner_one, note_one = recommendation(round_one)
display_round_one = round_one.rename(
    columns={
        "alternative": "Alternativa",
        "name": "Política",
        "score": "Puntaje",
        "feasible": "Viable",
        "constraint": "Lectura de restricciones",
    }
)
st.dataframe(
    display_round_one,
    hide_index=True,
    width="stretch",
    column_config={"Puntaje": st.column_config.NumberColumn(format="%.2f")},
)
score_figure = px.bar(
    round_one,
    x="alternative",
    y="score",
    color="feasible",
    hover_name="name",
    color_discrete_map={True: "#008dd2", False: "#aab8c2"},
    range_y=[0, 5],
    labels={"alternative": "Alternativa", "score": "Puntaje", "feasible": "Viable"},
    title="Comparación ponderada · decisión inicial",
)
score_figure.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(score_figure, use_container_width=True)
if winner_one:
    st.success(f"Lectura del modelo: alternativa {winner_one} · {ALTERNATIVES[winner_one]['name']}. {note_one}")
else:
    st.warning(note_one)
st.caption("El resultado ayuda a discutir; no reemplaza la evidencia, el contexto ni la responsabilidad de decidir.")

if st.button("Registrar como decisión inicial", type="primary", width="stretch"):
    st.session_state.student_a5_initial = {
        "winner": winner_one,
        "scores": round_one.to_dict("records"),
        "weights": dict(weights),
        "budget": budget,
        "risk": risk_tolerance,
        "horizon": horizon,
    }
    st.toast("Decisión inicial guardada solo durante esta sesión.")

st.markdown("### 3. Incorpora nueva evidencia")
st.caption("Selecciona el escenario indicado por el docente y observa exactamente qué supuesto cambia.")
scenario_labels = {"": "Sin nueva evidencia"} | {
    code: f"{code} · {details['title']}" for code, details in SCENARIOS.items()
}
scenario = st.selectbox(
    "Escenario de revisión",
    list(scenario_labels),
    format_func=lambda code: scenario_labels[code],
    key="student_a5_scenario",
)
selected_scenario = scenario or None
if selected_scenario:
    details = SCENARIOS[selected_scenario]
    st.warning(f"**{details['title']}** — {details['description']} {details['effect']}")

round_two = evaluate(weights, budget, risk_tolerance, horizon, selected_scenario)
winner_two, note_two = recommendation(round_two)
initial = st.session_state.get(
    "student_a5_initial",
    {"winner": winner_one, "scores": round_one.to_dict("records")},
)
comparison = (
    pd.DataFrame(initial["scores"])[["alternative", "score"]]
    .rename(columns={"score": "Decisión inicial"})
    .merge(
        round_two[["alternative", "score"]].rename(columns={"score": "Decisión revisada"}),
        on="alternative",
    )
    .melt("alternative", var_name="Momento", value_name="Puntaje")
)
comparison_figure = px.bar(
    comparison,
    x="alternative",
    y="Puntaje",
    color="Momento",
    barmode="group",
    color_discrete_sequence=["#88a7b8", "#f29400"],
    range_y=[0, 5],
    labels={"alternative": "Alternativa"},
    title="Decisión inicial → nueva evidencia → decisión revisada",
)
comparison_figure.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(comparison_figure, use_container_width=True)

initial_winner = initial.get("winner")
if selected_scenario and initial_winner != winner_two:
    st.warning(
        f"La alternativa priorizada cambia de {initial_winner or 'ninguna'} a {winner_two or 'ninguna'}. "
        "Explica qué supuesto produjo el cambio antes de aceptar la nueva recomendación."
    )
elif selected_scenario:
    st.info(f"La alternativa {winner_two or '—'} se mantiene. Comprueba si la diferencia sigue siendo suficientemente robusta. {note_two}")
else:
    st.info("Selecciona un escenario para poner a prueba la decisión inicial.")

st.markdown("### 4. Prueba la robustez")
sensitivity_table = sensitivity(weights, budget, risk_tolerance, horizon, selected_scenario)
winner_counts = (
    sensitivity_table.groupby("winner", as_index=False)
    .size()
    .rename(columns={"winner": "Alternativa", "size": "Variaciones"})
)
robustness_figure = px.bar(
    winner_counts,
    x="Alternativa",
    y="Variaciones",
    color="Alternativa",
    color_discrete_sequence=["#005293", "#008dd2", "#00a99d", "#f29400", "#aab8c2"],
    title="Ganador en 12 variaciones de sensibilidad",
)
robustness_figure.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(robustness_figure, use_container_width=True)
with st.expander("Ver detalle de sensibilidad"):
    detail = sensitivity_table.copy()
    detail["variation"] = detail["variation"].map(lambda value: f"{value:+d} puntos")
    st.dataframe(
        detail.rename(
            columns={"criterion": "Criterio alterado", "variation": "Variación", "winner": "Ganador", "note": "Lectura"}
        ),
        hide_index=True,
        width="stretch",
    )

st.markdown("### Cierre de la decisión")
st.markdown(
    "Responde con tu equipo: **¿qué recomendamos, qué evidencia respalda la decisión y qué podría hacernos cambiar?**"
)
questions = st.columns(3)
questions[0].info("**Trade-off**\n\n¿Qué beneficio priorizamos y qué costo aceptamos?")
questions[1].info("**Evidencia contraria**\n\n¿Qué información cuestiona nuestra elección?")
questions[2].info("**Condición de revisión**\n\n¿Qué señal obligaría a modificar o suspender la decisión?")
st.caption(
    "Secuencia EVIDA: Explorar · Ver evidencia · Identificar contradicciones y supuestos · Decidir · Argumentar. "
    "Ninguna selección se guarda en la base docente."
)
