from __future__ import annotations

import io
from textwrap import wrap
from pathlib import Path

import reportlab
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera", str(FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("Vera-Bold", str(FONT_DIR / "VeraBd.ttf")))
pdfmetrics.registerFont(TTFont("Vera-Italic", str(FONT_DIR / "VeraIt.ttf")))


def build_decision_pdf(record: dict) -> bytes:
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    page.setTitle("Actividad 05 - Ficha ejecutiva antes y después")

    def draw_header(page_number: int) -> float:
        page.setFillColor(HexColor("#041725"))
        page.rect(0, height - 112, width, 112, fill=1, stroke=0)
        page.setFillColor(HexColor("#F29400"))
        page.rect(42, height - 112, 110, 4, fill=1, stroke=0)
        page.setFillColor(HexColor("#FFFFFF"))
        page.setFont("Vera-Bold", 20)
        page.drawString(42, height - 50, "Ficha ejecutiva ANTES y DESPUÉS")
        page.setFillColor(HexColor("#BFE9FF"))
        page.setFont("Vera", 9)
        page.drawString(42, height - 73, "Actividad 05 - Farmacia Cruz Blanca - Diplomado UDD")
        page.drawString(42, height - 90, f"Equipo: {record.get('team', 'Sin identificar')} | Página {page_number}")
        return height - 145

    def draw_footer() -> None:
        page.setFillColor(HexColor("#5A6D79"))
        page.setFont("Vera-Italic", 8)
        page.drawString(42, 32, "La evidencia histórica y los supuestos didácticos se presentan por separado. La decisión final requiere revisión humana.")

    fields = [
        ("Integrantes", ", ".join(record.get("members", []))),
        ("Comparación de decisión", f"ANTES: {record.get('before', '-')} | DESPUÉS: {record.get('after', '-')}. Estrategia final: {record.get('strategy', '')}"),
        ("Descripción de la estrategia", record.get("strategy_description", "")),
        ("Evidencia histórica NPS", record.get("historical_evidence", "")),
        ("Supuesto didáctico de evaluación", record.get("strategy_assumption", "")),
        ("Beneficio y trade-off esperados", f"Beneficio: {record.get('strategy_benefit', '')} Trade-off: {record.get('strategy_tradeoff', '')}"),
        ("Evidencia que respalda la decisión", record.get("evidence", "")),
        ("Evidencia o límite que la cuestiona", record.get("contrary", "")),
        ("Principal trade-off identificado por el equipo", record.get("tradeoff", "")),
        ("Qué cambió con la nueva evidencia", record.get("change", "")),
        ("Condición para revisar o suspender", record.get("condition", "")),
    ]
    if record.get("strategy_code") == "D":
        fields.extend([
            ("Foco del diagnóstico", record.get("diagnostic_focus", "")),
            ("Evidencia necesaria", record.get("diagnostic_evidence", "")),
            ("Incertidumbre que busca reducir", record.get("diagnostic_uncertainty", "")),
        ])

    page_number = 1
    y = draw_header(page_number)
    for index, (label, value) in enumerate(fields, start=1):
        lines = wrap((value or "Sin completar").replace("\n", " "), width=94)
        required_height = 38 + 12 * min(len(lines), 8)
        if y - required_height < 42:
            draw_footer()
            page.showPage()
            page_number += 1
            y = draw_header(page_number)
        page.setFillColor(HexColor("#005293"))
        page.setFont("Vera-Bold", 10)
        page.drawString(42, y, f"{index}. {label}")
        y -= 16
        page.setFillColor(HexColor("#172B38"))
        page.setFont("Vera", 9)
        for line in lines[:8]:
            page.drawString(48, y, line)
            y -= 12
        y -= 10
        page.setStrokeColor(HexColor("#D5E2EA"))
        page.line(42, y + 4, width - 42, y + 4)
    draw_footer()
    page.save()
    return buffer.getvalue()
