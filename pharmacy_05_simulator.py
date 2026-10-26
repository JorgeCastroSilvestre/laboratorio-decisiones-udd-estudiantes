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
    "A": {"name": "Mejorar la atención", "description": "Reforzar protocolos, dotación y tiempos de atención.", "productivity": 4.0, "wellbeing": 5.0, "collaboration": 3.5, "budget_required": 3, "risk_level": 2, "days": 45, "blocked_by": "equipo_comercial_saturado"},
    "B": {"name": "Mejorar la disponibilidad", "description": "Reducir quiebres de stock y alinear inventario físico y sistemas.", "productivity": 5.0, "wellbeing": 4.5, "collaboration": 4.5, "budget_required": 4, "risk_level": 4, "days": 75, "blocked_by": "dependencia_proveedores"},
    "C": {"name": "Revisar precios y promociones", "description": "Revisar arquitectura de precios, beneficios y claridad de promociones.", "productivity": 3.5, "wellbeing": 4.0, "collaboration": 3.0, "budget_required": 5, "risk_level": 4, "days": 60, "blocked_by": "capacidad_analitica_limitada"},
    "D": {"name": "Realizar un diagnóstico focalizado", "description": "Levantar evidencia adicional antes de escalar una intervención.", "productivity": 2.5, "wellbeing": 2.5, "collaboration": 5.0, "budget_required": 1, "risk_level": 1, "days": 30, "blocked_by": "ninguna"},
}

SCENARIOS = {
    "demand_increase": {"title": "Aumento de demanda", "description": "La demanda proyectada aumenta y eleva la presión sobre sucursales e inventario.", "effect": "Favorece la capacidad de respuesta de B y reduce la suficiencia de una mejora centrada solo en atención."},
    "supply_issues": {"title": "Problemas de abastecimiento", "description": "Proveedores críticos informan plazos más largos e inciertos.", "effect": "Aumenta el valor de diagnosticar y coordinar, pero eleva el riesgo y plazo de B."},
    "budget_reduced": {"title": "Presupuesto reducido", "description": "La disponibilidad presupuestaria disminuye dos niveles.", "effect": "La restricción puede volver inviables alternativas intensivas en recursos; el presupuesto no cambia de peso."},
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
        changed["B"]["wellbeing"] = 5.0
        changed["A"]["productivity"] = 3.25
    elif scenario == "supply_issues":
        changed["B"]["risk_level"] = 5
        changed["B"]["days"] = 90
        changed["D"]["productivity"] = 3.5
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
        rows.append({"alternative": code, "name": values["name"], "score": round(score, 3), "feasible": not reasons, "constraint": ", ".join(reasons) or "Sin alerta", "budget_required": values["budget_required"], "risk_level": values["risk_level"], "days": values["days"]})
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
