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
    page.setTitle("Actividad 05 - Ficha ejecutiva")
    page.setFillColor(HexColor("#041725"))
    page.rect(0, height - 112, width, 112, fill=1, stroke=0)
    page.setFillColor(HexColor("#F29400"))
    page.rect(42, height - 112, 110, 4, fill=1, stroke=0)
    page.setFillColor(HexColor("#FFFFFF"))
    page.setFont("Vera-Bold", 20)
    page.drawString(42, height - 50, "Decisión estratégica con evidencia")
    page.setFillColor(HexColor("#BFE9FF"))
    page.setFont("Vera", 9)
    page.drawString(42, height - 73, "Actividad 05 - Farmacia Cruz Blanca - Diplomado UDD")
    page.drawString(42, height - 90, f"Equipo: {record.get('team', 'Sin identificar')} | Decisión: ANTES {record.get('before', '-')} > DESPUÉS {record.get('after', '-')}")

    fields = [
        ("Integrantes", ", ".join(record.get("members", []))),
        ("Estrategia seleccionada", record.get("strategy", "")),
        ("Evidencia que la respalda", record.get("evidence", "")),
        ("Evidencia que la cuestiona", record.get("contrary", "")),
        ("Principal tensión o costo", record.get("tradeoff", "")),
        ("Cambio observado", record.get("change", "")),
        ("Condición para revisar o suspender", record.get("condition", "")),
    ]
    y = height - 145
    for index, (label, value) in enumerate(fields, start=1):
        page.setFillColor(HexColor("#005293"))
        page.setFont("Vera-Bold", 10)
        page.drawString(42, y, f"{index}. {label}")
        y -= 16
        page.setFillColor(HexColor("#172B38"))
        page.setFont("Vera", 9)
        for line in wrap((value or "Sin completar").replace("\n", " "), width=94)[:4]:
            page.drawString(48, y, line)
            y -= 12
        y -= 10
        page.setStrokeColor(HexColor("#D5E2EA"))
        page.line(42, y + 4, width - 42, y + 4)
    page.setFillColor(HexColor("#5A6D79"))
    page.setFont("Vera-Italic", 8)
    page.drawString(42, 32, "Ficha generada desde el registro de la sesión. La decisión final requiere revisión humana.")
    page.save()
    return buffer.getvalue()
