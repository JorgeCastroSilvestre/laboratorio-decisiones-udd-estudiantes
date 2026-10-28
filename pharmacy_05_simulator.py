from __future__ import annotations

import pandas as pd


CRITERIA = ["productivity", "wellbeing", "collaboration"]
LABELS = {
    "productivity": "Productividad",
    "wellbeing": "Bienestar",
    "collaboration": "Colaboración",
}

# Puntajes 1-5: supuestos didácticos, separados de la evidencia observada.
ALTERNATIVES = {
    "A": {
        "name": "Espera y turnos",
        "description": "Optimizar tiempos de espera, distribución de turnos y procesos de atención.",
        "productivity": 4.5, "wellbeing": 4.6, "collaboration": 3.7,
        "budget_required": 3, "risk_level": 2, "days": 45,
        "blocked_by": "capacidad_operativa_limitada",
        "assumption": "Se supone que reorganizar flujos y turnos puede reducir esperas sin aumentar la dotación de forma permanente.",
        "benefit": "Mejora visible de la experiencia de atención y del uso de la capacidad disponible.",
        "tradeoff": "Puede trasladar carga entre horarios o equipos si no se mide la demanda por franja.",
    },
    "B": {
        "name": "Disponibilidad y stock",
        "description": "Mejorar reposición, inventario y disponibilidad de medicamentos.",
        "productivity": 4.8, "wellbeing": 4.0, "collaboration": 4.2,
        "budget_required": 4, "risk_level": 3, "days": 75,
        "blocked_by": "dependencia_proveedores",
        "assumption": "Se supone que una mejor coordinación de inventario y reposición disminuirá quiebres evitables.",
        "benefit": "Mayor disponibilidad y menos reprocesos asociados a búsquedas o sustituciones.",
        "tradeoff": "Exige inversión, calidad de datos y coordinación con proveedores que la farmacia no controla por completo.",
    },
    "C": {
        "name": "Orientación y seguimiento digital",
        "description": "Implementar herramientas digitales para informar, orientar y dar seguimiento a consultas de clientes.",
        "productivity": 3.9, "wellbeing": 4.4, "collaboration": 4.6,
        "budget_required": 4, "risk_level": 3, "days": 60,
        "blocked_by": "integracion_digital_limitada",
        "assumption": "Se supone que una herramienta simple y accesible resolverá consultas repetitivas y mejorará la continuidad del seguimiento.",
        "benefit": "Entrega información consistente, deriva mejor las consultas y mantiene trazabilidad del seguimiento.",
        "tradeoff": "Puede excluir a clientes con menor acceso digital y requiere integración, actualización de contenidos y resguardo de datos.",
    },
    "D": {
        "name": "Diagnóstico focalizado",
        "description": "Investigar una oportunidad A, B o C antes de realizar una inversión importante.",
        "productivity": 2.8, "wellbeing": 3.2, "collaboration": 4.3,
        "budget_required": 2, "risk_level": 1, "days": 30,
        "blocked_by": "capacidad_analitica_limitada",
        "assumption": "Se supone que treinta días de evidencia focalizada pueden reducir una incertidumbre decisiva antes de comprometer recursos mayores.",
        "benefit": "Reduce incertidumbre y permite diseñar una inversión más específica y revisable.",
        "tradeoff": "Posterga beneficios operativos y consume tiempo analítico; investigar no reemplaza decidir.",
    },
}

DIAGNOSTIC_FOCUS = {
    "A": {
        "label": "Espera y turnos",
        "evidence": "Tiempos de espera por franja, demanda, dotación, duración de atención y causas de abandono.",
        "uncertainty": "Si el problema principal proviene de la distribución de turnos, del flujo o de la capacidad disponible.",
    },
    "B": {
        "label": "Disponibilidad y stock",
        "evidence": "Quiebres por medicamento, tiempos de reposición, exactitud del inventario y causas atribuibles a proveedores o procesos internos.",
        "uncertainty": "Qué parte de la falta de disponibilidad puede resolver la farmacia y cuál depende de terceros.",
    },
    "C": {
        "label": "Orientación y seguimiento digital",
        "evidence": "Tipos y volumen de consultas, canales preferidos, capacidad de seguimiento, brechas digitales y requisitos de integración y privacidad.",
        "uncertainty": "Si una solución digital resolvería necesidades reales y sería adoptada por clientes y equipos.",
    },
}

SCENARIOS = {
    "demand_increase": {"title": "Aumento de demanda presencial", "description": "La demanda proyectada aumenta y eleva la presión sobre la atención y el inventario.", "effect": "Aumenta el valor de A y B; reduce la conveniencia de postergar toda intervención para investigar."},
    "supply_issues": {"title": "Problemas de abastecimiento", "description": "Proveedores críticos informan plazos más largos e inciertos.", "effect": "Eleva el riesgo y plazo de B; una orientación digital clara puede ayudar a informar alternativas, sin resolver el stock."},
    "digital_followup": {"title": "Brecha de orientación y seguimiento", "description": "Las consultas repetidas y la falta de seguimiento aparecen como una fricción relevante para clientes y equipos.", "effect": "Aumenta el beneficio potencial de C, pero mantiene las exigencias de integración, accesibilidad y privacidad."},
    "budget_reduced": {"title": "Presupuesto reducido", "description": "La disponibilidad presupuestaria disminuye dos niveles.", "effect": "Puede volver inviables A, B o C; D sigue teniendo costo y plazo propios y no reemplaza una decisión posterior."},
}

EVIDENCE = {
    "aggregates": [
        {"period": 2020, "valid": 235, "promoters": 95, "passives": 73, "detractors": 67, "nps": 11.9},
        {"period": 2021, "valid": 247, "promoters": 94, "passives": 91, "detractors": 62, "nps": 13.0},
    ],
    "topics": [
        {"period": 2020, "topic": "Atención", "mentions": 7},
        {"period": 2020, "topic": "Precios", "mentions": 12},
        {"period": 2020, "topic": "Disponibilidad", "mentions": 9},
        {"period": 2021, "topic": "Atención", "mentions": 4},
        {"period": 2021, "topic": "Precios", "mentions": 11},
        {"period": 2021, "topic": "Disponibilidad", "mentions": 8},
    ],
    "qualitative_comments": 28,
    "taxonomy_rows": 41922,
}


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(float(weights.get(key, 0)), 0) for key in CRITERIA)
    if not total:
        return {key: 1 / len(CRITERIA) for key in CRITERIA}
    return {key: max(float(weights.get(key, 0)), 0) / total for key in CRITERIA}


def apply_scenario(matrix: dict, scenario: str | None) -> dict:
    changed = {code: dict(values) for code, values in matrix.items()}
    if scenario == "demand_increase":
        changed["A"]["productivity"] = 5.0
        changed["B"]["wellbeing"] = 4.4
        changed["D"]["productivity"] = 2.4
    elif scenario == "supply_issues":
        changed["B"]["risk_level"] = 4
        changed["B"]["days"] = 90
        changed["C"]["collaboration"] = 4.8
        changed["D"]["productivity"] = 3.2
    elif scenario == "digital_followup":
        changed["C"]["productivity"] = 4.5
        changed["C"]["wellbeing"] = 4.9
        changed["C"]["collaboration"] = 5.0
        changed["D"]["wellbeing"] = 3.5
    return changed


def effective_budget(budget: int, scenario: str | None) -> int:
    return max(1, int(budget) - 2) if scenario == "budget_reduced" else int(budget)


def evaluate(weights: dict[str, float], budget: int, risk_tolerance: int = 3, horizon: int = 90, operational_restriction: str = "ninguna", scenario: str | None = None, matrix: dict | None = None) -> pd.DataFrame:
    source = apply_scenario(matrix or ALTERNATIVES, scenario)
    normalized = normalize_weights(weights)
    available_budget = effective_budget(budget, scenario)
    rows = []
    for code, values in source.items():
        score = sum(float(values[key]) * normalized[key] for key in CRITERIA)
        reasons = []
        if values["budget_required"] > available_budget:
            reasons.append("supera el presupuesto")
        if values["risk_level"] > risk_tolerance:
            reasons.append("supera la tolerancia al riesgo")
        if values["days"] > horizon:
            reasons.append("supera el horizonte")
        if operational_restriction != "ninguna" and values["blocked_by"] == operational_restriction:
            reasons.append("afectada por la restricción operativa")
        rows.append({"alternative": code, "name": values["name"], "score": round(score, 3), "feasible": not reasons, "constraint": ", ".join(reasons) or "Sin alerta", "budget_required": values["budget_required"], "risk_level": values["risk_level"], "days": values["days"], "benefit": values["benefit"], "tradeoff": values["tradeoff"]})
    return pd.DataFrame(rows).sort_values(["feasible", "score", "alternative"], ascending=[False, False, True], ignore_index=True)


def recommendation(results: pd.DataFrame, threshold: float = 0.15) -> tuple[str | None, str]:
    feasible = results[results["feasible"]]
    if feasible.empty:
        return None, "Ninguna estrategia cumple todas las restricciones. Revise alcance, recursos o plazo."
    best = feasible.iloc[0]
    if len(feasible) > 1 and float(best["score"] - feasible.iloc[1]["score"]) < threshold:
        return str(best["alternative"]), "Resultado sensible: las dos estrategias viables mejor evaluadas están muy próximas."
    return str(best["alternative"]), "La estrategia lidera con los supuestos actuales; todavía requiere juicio y trazabilidad."


def sensitivity(weights: dict[str, float], budget: int, risk_tolerance: int = 3, horizon: int = 90, operational_restriction: str = "ninguna", scenario: str | None = None) -> pd.DataFrame:
    rows = []
    for key in CRITERIA:
        for delta in (-2, 2):
            changed = dict(weights)
            changed[key] = max(0, changed.get(key, 0) + delta)
            results = evaluate(changed, budget, risk_tolerance, horizon, operational_restriction, scenario)
            winner, note = recommendation(results)
            rows.append({"criterion": LABELS[key], "variation": delta, "winner": winner or "—", "note": note})
    return pd.DataFrame(rows)


def decision_explanation(results: pd.DataFrame, weights: dict[str, float], scenario: str | None) -> str:
    winner, note = recommendation(results)
    if winner is None:
        return note
    normalized = normalize_weights(weights)
    primary = max(normalized, key=normalized.get)
    context = f" bajo el escenario {SCENARIOS[scenario]['title'].lower()}" if scenario else ""
    rejected = int((~results["feasible"]).sum())
    return f"{winner} · {ALTERNATIVES[winner]['name']} queda primera entre las alternativas viables{context}. La prioridad dominante es {LABELS[primary].lower()} ({normalized[primary] * 100:.0f}%). {rejected} alternativa(s) presentan restricciones. {note}"
