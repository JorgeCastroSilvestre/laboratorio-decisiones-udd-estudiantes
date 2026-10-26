from __future__ import annotations

import pandas as pd


CRITERIA = ["productivity", "collaboration", "wellbeing", "costs", "risk", "continuity"]
LABELS = {
    "productivity": "Productividad",
    "collaboration": "Colaboración",
    "wellbeing": "Bienestar",
    "costs": "Costos",
    "risk": "Riesgo",
    "continuity": "Continuidad operacional",
}
ALTERNATIVES = {
    "0": {
        "name": "Mantener situación actual",
        "productivity": 3,
        "collaboration": 3,
        "wellbeing": 3,
        "costs": 5,
        "risk": 4,
        "continuity": 4,
        "cost_level": 1,
        "risk_level": 1,
        "days": 0,
    },
    "A": {
        "name": "Presencialidad definida",
        "productivity": 4,
        "collaboration": 5,
        "wellbeing": 2,
        "costs": 2,
        "risk": 3,
        "continuity": 4,
        "cost_level": 4,
        "risk_level": 3,
        "days": 60,
    },
    "B": {
        "name": "Modelo híbrido estructurado",
        "productivity": 5,
        "collaboration": 4,
        "wellbeing": 4,
        "costs": 3,
        "risk": 4,
        "continuity": 5,
        "cost_level": 3,
        "risk_level": 2,
        "days": 45,
    },
    "C": {
        "name": "Flexibilidad por equipos",
        "productivity": 4,
        "collaboration": 2,
        "wellbeing": 5,
        "costs": 4,
        "risk": 2,
        "continuity": 3,
        "cost_level": 2,
        "risk_level": 4,
        "days": 30,
    },
}
SCENARIOS = {
    "A": {
        "title": "Restricción presupuestaria",
        "description": "El presupuesto disponible disminuye un 25%.",
        "effect": "Reduce la valoración de costos de A y B en un punto.",
    },
    "B": {
        "title": "Colaboración bajo presión",
        "description": "Una evaluación interna simulada identifica dificultades de coordinación entre equipos.",
        "effect": "C pierde un punto y B gana un punto en colaboración.",
    },
    "C": {
        "title": "Señal de bienestar",
        "description": "Una encuesta simulada muestra deterioro en la experiencia de áreas específicas.",
        "effect": "A pierde un punto y C gana medio punto en bienestar.",
    },
}


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(float(weights.get(key, 0)), 0) for key in CRITERIA)
    if not total:
        return {key: 1 / len(CRITERIA) for key in CRITERIA}
    return {key: max(float(weights.get(key, 0)), 0) / total for key in CRITERIA}


def apply_scenario(matrix: dict, scenario: str | None) -> dict:
    changed = {code: dict(values) for code, values in matrix.items()}
    if scenario == "A":
        changed["A"]["costs"] = max(1, changed["A"]["costs"] - 1)
        changed["B"]["costs"] = max(1, changed["B"]["costs"] - 1)
    elif scenario == "B":
        changed["C"]["collaboration"] = max(1, changed["C"]["collaboration"] - 1)
        changed["B"]["collaboration"] = min(5, changed["B"]["collaboration"] + 1)
    elif scenario == "C":
        changed["A"]["wellbeing"] = max(1, changed["A"]["wellbeing"] - 1)
        changed["C"]["wellbeing"] = min(5, changed["C"]["wellbeing"] + 0.5)
    return changed


def evaluate(
    weights: dict[str, float],
    budget: int,
    risk_tolerance: int,
    horizon: int,
    scenario: str | None = None,
    matrix: dict | None = None,
) -> pd.DataFrame:
    source = apply_scenario(matrix or ALTERNATIVES, scenario)
    normalized = normalize_weights(weights)
    rows = []
    for code, values in source.items():
        score = sum(float(values[key]) * normalized[key] for key in CRITERIA)
        reasons = []
        if values["cost_level"] > budget:
            reasons.append("supera presupuesto")
        if values["risk_level"] > risk_tolerance:
            reasons.append("supera tolerancia al riesgo")
        if values["days"] > horizon:
            reasons.append("supera horizonte")
        rows.append(
            {
                "alternative": code,
                "name": values["name"],
                "score": round(score, 3),
                "feasible": not reasons,
                "constraint": ", ".join(reasons) or "Sin alerta",
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["feasible", "score", "alternative"],
        ascending=[False, False, True],
        ignore_index=True,
    )


def recommendation(results: pd.DataFrame, threshold: float = 0.15) -> tuple[str | None, str]:
    feasible = results[results["feasible"]]
    if feasible.empty:
        return None, "Ninguna alternativa cumple todas las restricciones; es necesario revisar los supuestos."
    if len(feasible) > 1 and float(feasible.iloc[0]["score"] - feasible.iloc[1]["score"]) < threshold:
        return str(feasible.iloc[0]["alternative"]), "Resultado sensible: las dos mejores alternativas están muy próximas."
    return str(feasible.iloc[0]["alternative"]), "Resultado estable bajo los supuestos actuales; todavía requiere juicio profesional."


def sensitivity(
    weights: dict[str, float],
    budget: int,
    risk_tolerance: int,
    horizon: int,
    scenario: str | None = None,
) -> pd.DataFrame:
    rows = []
    for key in CRITERIA:
        for delta in (-2, 2):
            changed = dict(weights)
            changed[key] = max(0, changed.get(key, 0) + delta)
            results = evaluate(changed, budget, risk_tolerance, horizon, scenario)
            winner, note = recommendation(results)
            rows.append(
                {
                    "criterion": LABELS[key],
                    "variation": delta,
                    "winner": winner or "—",
                    "note": note,
                }
            )
    return pd.DataFrame(rows)
