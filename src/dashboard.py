"""Visual KPI report for the PRO'FIT'EIN operations sample.

Public facts used as the frame: Pro'FIT'ein is a Hyderabad macro-counted meal
service, and a diet kitchen is listed in Boduppal. The delivery rows themselves
are not published, so this report computes every chart from the sample database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "profitein.sqlite"
OUT = ROOT / "output" / "dashboard.html"

PALETTE = ["#118DFF", "#12239E", "#E66C37", "#6B007B", "#1AAB40", "#D9B300", "#E044A7", "#744EC2"]
TEMPLATE = "plotly_white"


def connect() -> sqlite3.Connection:
    if not DB.exists():
        from src.build_profitein import build

        build()
    return sqlite3.connect(DB)


def read(con: sqlite3.Connection, sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, con)


def style(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template=TEMPLATE,
        height=height,
        margin=dict(l=20, r=20, t=56, b=20),
        legend=dict(orientation="h", y=-0.2),
        font=dict(family="Segoe UI, sans-serif", size=13),
        colorway=PALETTE,
    )
    return fig


def load_frames(con: sqlite3.Connection) -> dict[str, pd.DataFrame]:
    return {
        "headline": read(
            con,
            """
            SELECT COUNT(*) AS deliveries,
                   ROUND(100.0 * AVG(otif_flag), 1) AS otif_pct,
                   ROUND(100.0 * AVG(perfect_flag), 1) AS perfect_pct,
                   ROUND(100.0 * AVG(complaint_flag), 1) AS complaint_pct,
                   ROUND(100.0 * AVG(change_flag), 1) AS change_pct,
                   ROUND(SUM(net_value_inr), 0) AS revenue_inr
            FROM vw_perfect
            """,
        ),
        "month": read(
            con,
            """
            SELECT year_month,
                   SUM(deliveries) AS deliveries,
                   ROUND(SUM(otif_pct * deliveries) / SUM(deliveries), 1) AS otif_pct,
                   ROUND(SUM(perfect_pct * deliveries) / SUM(deliveries), 1) AS perfect_pct,
                   ROUND(SUM(complaint_pct * deliveries) / SUM(deliveries), 1) AS complaint_pct,
                   ROUND(SUM(change_pct * deliveries) / SUM(deliveries), 1) AS change_pct
            FROM vw_month_zone
            GROUP BY year_month
            ORDER BY year_month
            """,
        ),
        "zone": read(
            con,
            """
            SELECT zone_name, band,
                   SUM(deliveries) AS deliveries,
                   ROUND(SUM(otif_pct * deliveries) / SUM(deliveries), 1) AS otif_pct,
                   ROUND(SUM(complaint_pct * deliveries) / SUM(deliveries), 1) AS complaint_pct,
                   ROUND(SUM(revenue_inr), 0) AS revenue_inr
            FROM vw_month_zone
            GROUP BY zone_name, band
            ORDER BY otif_pct
            """,
        ),
        "heat": read(
            con,
            """
            SELECT year_month, zone_name, otif_pct
            FROM vw_month_zone
            """,
        ),
        "reasons": read(con, "SELECT reason, complaints, share_pct FROM vw_complaint_pareto"),
        "reason_zone": read(
            con,
            """
            SELECT z.zone_name, z.band, c.reason, COUNT(*) AS complaints
            FROM complaints c
            JOIN deliveries d ON d.delivery_id = c.delivery_id
            JOIN subscribers s ON s.subscriber_id = d.subscriber_id
            JOIN zones z ON z.zone_id = s.zone_id
            GROUP BY z.zone_name, z.band, c.reason
            """,
        ),
        "changes": read(
            con,
            "SELECT change_type, COUNT(*) AS changes FROM plan_changes GROUP BY change_type ORDER BY changes DESC",
        ),
        "plan": read(
            con,
            """
            SELECT plan_name,
                   COUNT(*) AS deliveries,
                   ROUND(100.0 * AVG(otif_flag), 1) AS otif_pct,
                   ROUND(100.0 * AVG(complaint_flag), 1) AS complaint_pct
            FROM vw_perfect
            GROUP BY plan_name
            """,
        ),
        "dq": read(
            con,
            "SELECT rule_name, COUNT(*) AS exceptions FROM dq_exceptions GROUP BY rule_name ORDER BY exceptions DESC",
        ),
        "tco": read(
            con,
            """
            SELECT material, supplier_name, unit_price_inr, freight_per_unit,
                   lead_time_days, ppm, tco_inr, eligible, otif_pct
            FROM vw_tco
            """,
        ),
        "risk": read(con, "SELECT risk_id, initiative, score, band, status FROM vw_risk ORDER BY score"),
        "counts": read(
            con,
            """
            SELECT
                (SELECT COUNT(*) FROM deliveries) AS trusted,
                (SELECT COUNT(*) FROM dq_exceptions) AS rejected
            """,
        ),
    }


def figures(frames: dict[str, pd.DataFrame]) -> list[tuple[str, go.Figure]]:
    month = frames["month"]
    zone = frames["zone"]
    trend = style(
        px.line(
            month.melt("year_month", ["otif_pct", "perfect_pct", "complaint_pct", "change_pct"], var_name="KPI", value_name="Percent"),
            x="year_month",
            y="Percent",
            color="KPI",
            markers=True,
            title="Univariate trend · service level and customer friction by month",
        )
    )
    trend.update_xaxes(title=None)
    bars = style(
        px.bar(
            zone.sort_values("otif_pct"),
            x="otif_pct",
            y="zone_name",
            color="band",
            orientation="h",
            text="otif_pct",
            title="On-time in-full by Hyderabad zone",
        )
    )
    bars.update_traces(textposition="outside")
    donut = style(
        px.pie(
            frames["reasons"],
            names="reason",
            values="complaints",
            hole=0.55,
            title="Complaint mix · why the subscriber wrote in",
            color_discrete_sequence=PALETTE,
        )
    )
    heat = frames["heat"].pivot(index="zone_name", columns="year_month", values="otif_pct")
    heatmap = style(
        go.Figure(
            data=go.Heatmap(
                z=heat.values,
                x=list(heat.columns),
                y=list(heat.index),
                colorscale=[[0, "#E66C37"], [0.5, "#F3E6C8"], [1, "#118DFF"]],
                colorbar=dict(title="OTIF %"),
                hovertemplate="Zone %{y}<br>%{x}<br>OTIF %{z:.1f}%<extra></extra>",
            )
        ),
        height=460,
    )
    heatmap.update_layout(title="Multivariate · on-time by zone and month")
    corr = round(zone["deliveries"].corr(zone["complaint_pct"]), 2)
    scatter = style(
        px.scatter(
            zone,
            x="deliveries",
            y="complaint_pct",
            color="band",
            size="revenue_inr",
            hover_name="zone_name",
            title=f"Bivariate · volume against complaint rate (correlation {corr})",
        )
    )
    scatter.update_xaxes(title="Trusted deliveries")
    scatter.update_yaxes(title="Complaint %")
    stacked = style(
        px.bar(
            frames["reason_zone"],
            x="zone_name",
            y="complaints",
            color="reason",
            title="Multivariate · complaint reason inside each zone",
        )
    )
    stacked.update_xaxes(title=None, tickangle=-30)
    plans = style(
        px.bar(
            frames["plan"],
            x="plan_name",
            y=["otif_pct", "complaint_pct"],
            barmode="group",
            title="Plan type · fat loss, muscle gain, clean eating",
        )
    )
    plans.update_xaxes(title=None)
    plans.update_yaxes(title="%")
    changes = style(
        px.pie(
            frames["changes"],
            names="change_type",
            values="changes",
            hole=0.45,
            title="Plan changes · the order-change KPI",
            color_discrete_sequence=PALETTE,
        )
    )
    quotes = quote_chart(frames["tco"])
    risks = style(
        px.bar(
            frames["risk"],
            x="score",
            y="risk_id",
            color="band",
            orientation="h",
            hover_data=["initiative", "status"],
            title="Risk score · probability × impact",
            color_discrete_map={"High": "#E66C37", "Medium": "#D9B300", "Low": "#1AAB40"},
        )
    )
    dq = style(
        px.bar(
            frames["dq"],
            x="exceptions",
            y="rule_name",
            orientation="h",
            title="Rows kept out of every chart above",
        )
    )
    return [
        ("Service trend", trend),
        ("Zone comparison", bars),
        ("Complaint mix", donut),
        ("Zone-month heatmap", heatmap),
        ("Volume and complaints", scatter),
        ("Reason by zone", stacked),
        ("Plan comparison", plans),
        ("Plan changes", changes),
        ("Ingredient total cost", quotes),
        ("Risk register", risks),
        ("Data quality", dq),
    ]


def _rupees(value: float) -> str:
    amount = round(float(value), 1)
    return str(int(amount)) if amount == int(amount) else f"{amount:.1f}"


def quote_chart(quotes_df: pd.DataFrame) -> go.Figure:
    """One panel per ingredient. Blue is the written price. Orange is the rest of the cost."""
    frame = quotes_df.copy()
    frame["eligible"] = frame["eligible"].astype(int)
    frame["extra_inr"] = (frame["tco_inr"] - frame["unit_price_inr"]).round(2)
    order = ["Chicken", "Paneer", "Millets and rice", "Meal box"]
    winners = (
        frame[frame["eligible"] == 1]
        .sort_values("tco_inr")
        .groupby("material", observed=True)
        .first()
    )
    winner_of = {material: row.supplier_name for material, row in winners.iterrows()}

    def y_label(row: pd.Series) -> str:
        parts = [row.supplier_name]
        if row.eligible != 1:
            parts.append("not eligible")
        if winner_of.get(row.material) == row.supplier_name:
            parts.append("award")
        return "  ·  ".join(parts)

    frame["supplier"] = frame.apply(y_label, axis=1)
    chart = make_subplots(rows=4, cols=1, subplot_titles=order, vertical_spacing=0.08)
    for index, material in enumerate(order, start=1):
        part = frame[frame["material"] == material].sort_values("tco_inr", ascending=False)
        detail = [
            (
                f"{row.supplier_name}<br>"
                f"Unit price ₹{row.unit_price_inr:.1f}<br>"
                f"Freight ₹{row.freight_per_unit:.1f}<br>"
                f"On time {row.otif_pct:.1f}% · lead time {int(row.lead_time_days)} days<br>"
                f"Orange extra ₹{row.extra_inr:.1f} · total ₹{row.tco_inr:.1f}"
            )
            for row in part.itertuples()
        ]
        chart.add_trace(
            go.Bar(
                y=part["supplier"],
                x=part["unit_price_inr"],
                orientation="h",
                name="Unit price",
                marker_color="#118DFF",
                text=[_rupees(value) for value in part["unit_price_inr"]],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="white", size=12),
                hovertext=detail,
                hoverinfo="text",
                legendgroup="price",
                showlegend=index == 1,
            ),
            row=index,
            col=1,
        )
        chart.add_trace(
            go.Bar(
                y=part["supplier"],
                x=part["extra_inr"],
                orientation="h",
                name="Extra, then the full cost",
                marker_color="#E66C37",
                text=[f"full cost {_rupees(value)}" for value in part["tco_inr"]],
                textposition="outside",
                cliponaxis=False,
                textfont=dict(size=12),
                hovertext=detail,
                hoverinfo="text",
                legendgroup="extra",
                showlegend=index == 1,
            ),
            row=index,
            col=1,
        )
        chart.update_xaxes(range=[0, float(part["tco_inr"].max()) * 1.32], row=index, col=1)
    chart.update_layout(
        barmode="stack",
        template=TEMPLATE,
        height=980,
        margin=dict(l=8, r=28, t=64, b=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=None),
        font=dict(family="Segoe UI, sans-serif", size=13),
        title=dict(text="Ingredient quotes", x=0, xanchor="left"),
    )
    chart.update_yaxes(title=None)
    return chart


def write_html(frames: dict[str, pd.DataFrame], charts: list[tuple[str, go.Figure]]) -> Path:
    headline = frames["headline"].iloc[0]
    counts = frames["counts"].iloc[0]
    trusted_share = round(100 * counts.trusted / (counts.trusted + counts.rejected), 1)
    blocks = []
    first = True
    for _, fig in charts:
        blocks.append(fig.to_html(full_html=False, include_plotlyjs="cdn" if first else False))
        first = False
    cards = [
        ("On-time, in-full", f"{headline.otif_pct}%", "Liefertreue"),
        ("Perfect delivery", f"{headline.perfect_pct}%", "No complaint, no change"),
        ("Complaint rate", f"{headline.complaint_pct}%", "Reklamationsquote"),
        ("Plan-change rate", f"{headline.change_pct}%", "Auftragsänderung"),
        ("Trusted share", f"{trusted_share}%", f"{int(counts.rejected):,} rows quarantined"),
    ]
    card_html = "".join(
        f"<div class='kpi'><span>{label}</span><b>{value}</b><em>{note}</em></div>"
        for label, value, note in cards
    )
    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>PRO'FIT'EIN KPI dashboard</title>
<style>
  body {{ margin: 0; background: #f3f2f1; color: #252423; font-family: "Segoe UI", sans-serif; }}
  header, main {{ max-width: 1180px; margin: 0 auto; padding: 20px 24px; }}
  h1 {{ margin: 0 0 6px; font-weight: 650; letter-spacing: -0.03em; }}
  .meta {{ color: #605e5c; font-size: 14px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 16px 0; }}
  .kpi {{ background: white; padding: 14px; border-top: 4px solid #118DFF; }}
  .kpi span, .kpi em {{ display: block; font-size: 11px; letter-spacing: .04em; text-transform: uppercase; color: #605e5c; font-style: normal; }}
  .kpi b {{ font-size: 28px; }}
  .note, .decision {{ background: white; padding: 14px 16px; margin: 12px 0 18px; }}
  .decision {{ border-left: 4px solid #12239E; }}
  .charts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  .charts > div {{ background: white; }}
  .wide {{ grid-column: 1 / -1; }}
</style>
</head>
<body>
<header>
  <p class="meta">PRO'FIT'EIN · Boduppal kitchen · Hyderabad delivery · February 2025 to March 2026</p>
  <h1>Customer experience of the meal, not the activity of the kitchen.</h1>
  <p class="note">The kitchen listing in Boduppal and the macro-counted meal offer are public. The delivery ledger is not. Every chart is computed from the portfolio sample with the SQL in <code>sql/002_views.sql</code>. Read the rates off this page. They are the sample, not a substitute for a figure on the CV.</p>
  <div class="kpis">{card_html}</div>
  <div class="decision">
    <b>What a C-level review would decide</b>
    <ol>
      <li>No new outer zone until the next monsoon has run on the split route. June 2025 is the evidence, not a closed chapter.</li>
      <li>One on-time definition. The private Sunday sheet is a second population and it leaves the scorecard.</li>
      <li>Ingredient awards use total cost. A chat price under 93% on-time does not reopen the RFQ.</li>
    </ol>
  </div>
</header>
<main>
  <div class="charts">
    {''.join(
        (
            '<div class="wide"><p class="note"><b>How to read the quote chart.</b> '
            'Each ingredient has its own three suppliers. '
            'Blue is the unit price on the quote. '
            'Orange is the extra: freight, a penalty for rejects, and the cost of waiting for the lead time. '
            'The white number is the unit price. The number after the orange tip is the full cost. '
            'Not eligible means under 93% on time, so the cheaper blue bar cannot win. '
            'Award is the eligible supplier with the lowest full cost.</p>'
            f'{block}</div>'
        )
        if index == 8
        else f'<div class="{"wide" if index in (0, 3) else ""}">{block}</div>'
        for index, block in enumerate(blocks)
    )}
  </div>
</main>
</body>
</html>
"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(document)
    return OUT


def main() -> None:
    with connect() as con:
        frames = load_frames(con)
    path = write_html(frames, figures(frames))
    print(path)


if __name__ == "__main__":
    main()
