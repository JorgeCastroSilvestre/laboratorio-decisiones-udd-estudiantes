from __future__ import annotations

from pathlib import Path
import sys

import streamlit as st


PORTAL_ROOT = Path(__file__).resolve().parent
if str(PORTAL_ROOT) not in sys.path:
    sys.path.insert(0, str(PORTAL_ROOT))

from portal_auth import require_student_access
from portal_common import VISIBLE_ACTIVITY_NUMBERS


st.set_page_config(page_title="Laboratorio de Decisiones con IA | Portal de Estudiantes UDD", layout="wide")
st.markdown(
    """
    <style>
      :root { --udd:#005293; --sky:#008dd2; --orange:#f29400; --ink:#081c2b; --paper:#f3f7fa; --line:#d5e2ea; }
      html, body, [class*="css"] { font-family: Inter, "Segoe UI", Arial, sans-serif; }
      .stApp { color:var(--ink); background:radial-gradient(circle at 85% 4%,rgba(0,141,210,.12),transparent 25rem),var(--paper); }
      .block-container { max-width:1320px; padding-top:2rem; padding-bottom:4rem; }
      [data-testid="stSidebar"] { background:linear-gradient(180deg,#041725,#082b43); border-right:1px solid rgba(0,141,210,.35); }
      [data-testid="stSidebar"] * { color:#eef8fd; }
      [data-testid="stSidebarNav"] a:hover { background:rgba(0,141,210,.14); }
      .portal-hero { position:relative; overflow:hidden; color:#fff; border-radius:18px; padding:2.1rem 2.2rem; margin-bottom:1.5rem;
        background:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px),radial-gradient(circle at 88% 18%,rgba(0,141,210,.55),transparent 18rem),linear-gradient(125deg,#041725,#005293);
        background-size:28px 28px,28px 28px,auto,auto; box-shadow:0 18px 45px rgba(0,48,84,.17); }
      .portal-hero:after { content:""; position:absolute; left:2.2rem; bottom:0; width:100px; height:3px; background:var(--orange); box-shadow:0 0 18px rgba(242,148,0,.8); }
      .portal-hero small { color:#75d1ff; font-weight:750; letter-spacing:.12em; text-transform:uppercase; }
      .portal-hero h1 { color:#fff; font-size:clamp(2rem,4vw,3.5rem); line-height:1.04; letter-spacing:-.045em; margin:.7rem 0; }
      .portal-hero p { color:#d7e7ef; font-size:1.04rem; max-width:850px; }
      [data-testid="stMetric"] { min-height:120px; background:rgba(255,255,255,.84); border:1px solid rgba(0,82,147,.16); border-radius:12px; padding:1rem; box-shadow:0 12px 30px rgba(0,82,147,.07); }
      [data-testid="stMetric"]:before { content:""; position:absolute; inset:0 auto 0 0; width:3px; background:linear-gradient(var(--sky),var(--orange)); }
      .activity-card { min-height:170px; background:rgba(255,255,255,.86); border:1px solid rgba(0,82,147,.16); border-radius:14px; padding:1.2rem; box-shadow:0 12px 30px rgba(0,82,147,.06); }
      .activity-card small { color:var(--sky); font-weight:750; letter-spacing:.1em; }
      .activity-card h3 { color:var(--ink); margin:.45rem 0; }
      .activity-card p { color:#5b6975; font-size:.88rem; }
      .activity-card .status { display:inline-block; border-radius:999px; padding:.25rem .55rem; color:var(--udd); background:#e5f3fa; font-size:.76rem; }
      h2,h3 { letter-spacing:-.025em; }
      [data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:10px; overflow:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("**Portal de Estudiantes**")
    st.caption("Diplomado UDD · Solo lectura")

navigation = st.navigation(
    {
        "Laboratorio": [st.Page("pages/inicio.py", title="Inicio", default=True)],
        "Actividades publicadas": [
            st.Page(f"pages/actividad_{number:02d}.py", title=f"Actividad {number}")
            for number in VISIBLE_ACTIVITY_NUMBERS
        ],
    }
)
require_student_access()
navigation.run()
