"""One-page visual KPI report for the PRO'FIT'EIN sample."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import streamlit as st

from src.dashboard import connect, figures, load_frames

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="PRO'FIT'EIN KPI dashboard", layout="wide")
st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; max-width: 1200px; }
    div[data-testid="stMetric"] { background: white; border-top: 4px solid #118DFF; padding: 10px 12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

with connect() as con:
    frames = load_frames(con)
headline = frames["headline"].iloc[0]
counts = frames["counts"].iloc[0]
trusted_share = round(100 * counts.trusted / (counts.trusted + counts.rejected), 1)

st.title("PRO'FIT'EIN · delivery KPI dashboard")
st.caption(
    "Boduppal kitchen is a public listing. The delivery rows are a sample, computed in SQL, "
    "February 2025 – March 2026. Henkel would recognise this as one definition, a customer outcome, and a risk with an owner."
)
cols = st.columns(5)
cols[0].metric("On-time in-full %  ·  Liefertreue", headline.otif_pct)
cols[1].metric("Perfect delivery %", headline.perfect_pct)
cols[2].metric("Complaint %  ·  Reklamationsquote", headline.complaint_pct)
cols[3].metric("Plan-change %", headline.change_pct)
cols[4].metric("Trusted share %", trusted_share)
st.info(
    "Three decisions: do not open another outer zone before the next monsoon test; "
    "retire the second spreadsheet so there is one on-time number; award ingredients on total cost, not the lowest chat price."
)
for title, fig in figures(frames):
    if title == "Ingredient total cost":
        st.markdown(
            "**How to read the quote chart.** "
            "Each ingredient has its own three suppliers. "
            "The blue bar is the unit price written on the quote. "
            "The orange tip is the extra cost: freight, a penalty for rejects, and the cost of waiting out the lead time. "
            "The white number is the unit price. The number after the orange tip is the full cost. "
            "A supplier marked **not eligible** was on time less than 93% of the time, so the cheaper blue bar cannot win. "
            "**Award** is the eligible supplier with the lowest full cost."
        )
    st.plotly_chart(fig, width="stretch")
with st.expander("SQL that these charts are not allowed to disagree with"):
    st.code((ROOT / "sql" / "002_views.sql").read_text(), language="sql")
    st.markdown(
        "On-time, in-full is arrived at or before the promised time and the meal delivered. "
        "Perfect delivery also has no complaint and no plan change. Quarantined rows never enter `vw_perfect`."
    )
