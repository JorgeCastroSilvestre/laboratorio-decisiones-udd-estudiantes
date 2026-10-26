from __future__ import annotations

import io
from textwrap import wrap

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_decision_pdf(record: dict) -> bytes:
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    page.setTitle("Actividad 05 - Ficha ejecutiva")
    page.setFillColor(HexColor("#041725"))
    page.rect(0, height - 112, width, 112, fill=1, stroke=0)
    page.setFillColor(HexColor("#F29400"))
    page.rect(42, height - 112, 110, 4, fill=1, stroke=0)
    page.setFillColor(HexColor("#FFFFFF"))
    page.setFont("Helvetica-Bold", 20)
    page.drawString(42, height - 50, "Decision estrategica con evidencia")
    page.setFillColor(HexColor("#BFE9FF"))
    page.setFont("Helvetica", 9)
    page.drawString(42, height - 73, "Actividad 05 - Farmacia Cruz Blanca - Diplomado UDD")
    page.drawString(42, height - 90, f"Equipo: {record.get('team', 'Sin identificar')} | Momento: decision revisada")

    fields = [
        ("Estrategia seleccionada", record.get("strategy", "")),
        ("Evidencia que la respalda", record.get("evidence", "")),
        ("Evidencia que la cuestiona", record.get("contrary", "")),
        ("Principal trade-off", record.get("tradeoff", "")),
        ("Cambio observado", record.get("change", "")),
        ("Condicion para revisar o suspender", record.get("condition", "")),
    ]
    y = height - 145
    for index, (label, value) in enumerate(fields, start=1):
        page.setFillColor(HexColor("#005293"))
        page.setFont("Helvetica-Bold", 10)
        page.drawString(42, y, f"{index}. {label}")
        y -= 16
        page.setFillColor(HexColor("#172B38"))
        page.setFont("Helvetica", 9)
        for line in wrap((value or "Sin completar").replace("\n", " "), width=94)[:5]:
            page.drawString(48, y, line)
            y -= 12
        y -= 10
        page.setStrokeColor(HexColor("#D5E2EA"))
        page.line(42, y + 4, width - 42, y + 4)
    page.setFillColor(HexColor("#5A6D79"))
    page.setFont("Helvetica-Oblique", 8)
    page.drawString(42, 32, "Ficha generada desde el registro de la sesion. La decision final requiere revision humana.")
    page.save()
    return buffer.getvalue()
