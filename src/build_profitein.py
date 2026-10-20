"""PRO'FIT'EIN Hyderabad meal-fulfillment KPI sample.

Subscribers, kitchens, and prices are generated. The file is a portfolio model of
the operations dashboard described for this role: one trusted KPI layer, a
kitchen-automation project record, and an ingredient RFQ comparison.
"""

from __future__ import annotations

import html
import random
import sqlite3
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql"
DATA = ROOT / "data"
OUT = ROOT / "output"
SEED = 42

ZONES = [
    ("GCB", "Gachibowli", "Core"),
    ("HTC", "Hitech City", "Core"),
    ("KDP", "Kondapur", "Core"),
    ("MDP", "Madhapur", "Core"),
    ("KKP", "Kukatpally", "Outer"),
    ("BNJ", "Banjara Hills", "Core"),
    ("JBH", "Jubilee Hills", "Core"),
    ("MNK", "Manikonda", "Outer"),
]

MEALS = [
    ("ML-01", "High-protein lunch bowl", "Lunch", 249),
    ("ML-02", "Millet breakfast box", "Breakfast", 179),
    ("ML-03", "Paneer dinner box", "Dinner", 269),
    ("ML-04", "Chicken meal prep", "Lunch", 299),
    ("ML-05", "Family add-on thali", "Dinner", 349),
    ("ML-06", "Whey shake pack", "Add-on", 149),
]

PLANS = ["Fat loss", "Muscle gain", "Clean eating"]


def month_starts(start: date, end: date):
    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        yield cursor
        cursor = date(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1)


def stamp(day: date, hour: int, minute: int) -> str:
    return datetime(day.year, day.month, day.day, hour, minute).strftime("%Y-%m-%d %H:%M")


def governance():
    initiatives = [
        (
            "INI-01",
            "Kitchen-plan automation",
            "Replace the morning spreadsheet with one plan the kitchen, procurement, and dispatch all use.",
            "Founder",
            "Operations lead",
            "Green",
            "2025-07-07",
            "2025-10-15",
            "Days from freeze to dispatch release",
            "Live since 15 October 2025. The old sheet is closed. Status now comes from this KPI layer.",
        ),
        (
            "INI-02",
            "Trusted delivery scorecard",
            "One on-time definition for leadership, kitchen, and the delivery partners.",
            "Operations lead",
            "Operations lead",
            "Green",
            "2025-03-01",
            "2025-05-30",
            "Share of rows in the trusted layer",
            "Exceptions stay in dq_exceptions. The scorecard reads vw_perfect only.",
        ),
        (
            "INI-03",
            "Wrong-meal control",
            "Cut wrong-meal and wrong-macro complaints by locking the plan change before the cook starts.",
            "Kitchen lead",
            "Operations lead",
            "Green",
            "2025-08-01",
            "2025-11-30",
            "Wrong-meal complaints",
            "From 12 November 2025 a plan change after 18:00 does not enter the next day's cook.",
        ),
        (
            "INI-04",
            "Monsoon dispatch cover",
            "Keep outer-zone breakfast promises when the rain adds a stop.",
            "Dispatch lead",
            "Operations lead",
            "Amber",
            "2025-06-01",
            "2026-03-31",
            "On-time % in Kukatpally and Manikonda",
            "June and July 2025 show the gap. The 2026 cover plan is written. It is not yet tested by a full monsoon.",
        ),
        (
            "INI-05",
            "Ingredient RFQ reset",
            "Award chicken, paneer, grain, and meal boxes on total cost and on-time history, not on the lowest message in the vendor chat.",
            "Procurement",
            "Operations lead",
            "Green",
            "2026-01-06",
            "2026-02-20",
            "Cost per shipped meal on awarded inputs",
            "Awards are in vw_tco. A supplier under 93% on-time is not eligible.",
        ),
    ]
    milestones = [
        ("MS-01", "INI-01", "Current-state map of the morning spreadsheet", "2025-07-18", "Done", "Operations lead"),
        ("MS-02", "INI-01", "Kitchen, procurement, and dispatch sign the new plan fields", "2025-08-29", "Done", "Kitchen lead"),
        ("MS-03", "INI-01", "Parallel run, two weeks", "2025-09-30", "Done", "Operations lead"),
        ("MS-04", "INI-01", "Spreadsheet retired", "2025-10-15", "Done", "Founder"),
        ("MS-05", "INI-02", "Five data-quality rules signed", "2025-04-11", "Done", "Operations lead"),
        ("MS-06", "INI-03", "18:00 change cutoff live", "2025-11-12", "Done", "Kitchen lead"),
        ("MS-07", "INI-04", "Outer-zone route split written", "2026-02-27", "Done", "Dispatch lead"),
        ("MS-08", "INI-04", "First monsoon week under the new route split", "2026-06-30", "At risk", "Dispatch lead"),
        ("MS-09", "INI-05", "Quotes scored on total cost", "2026-02-20", "Done", "Procurement"),
    ]
    risks = [
        ("R-01", "INI-04", "The route split is untested until the next monsoon. Outer-zone lateness can return in June 2026.", 3, 5, "Do not add a new outer zone before the June review. Keep a 20-minute buffer on Kukatpally and Manikonda breakfast slots.", "Dispatch lead", "Open"),
        ("R-02", "INI-01", "One dispatcher still keeps a private copy of the old sheet for Sunday volumes.", 2, 4, "Name that sheet in the next Monday review and close it. Two plans means two on-time numbers.", "Operations lead", "Open"),
        ("R-03", "INI-03", "Subscribers still message a meal swap after the cutoff and expect the kitchen to absorb it.", 3, 3, "The app confirms the cutoff. A late swap is tomorrow's meal, not a complaint against tonight's box.", "Kitchen lead", "Mitigating"),
        ("R-04", "INI-05", "A lower unit price will reappear in the vendor chat without freight or reject history.", 2, 4, "No award outside vw_tco. Chat prices are not a second scorecard.", "Procurement", "Open"),
    ]
    lessons = [
        ("The morning plan was a kitchen document. Promise times lived in another sheet, so a late van was discovered by the subscriber.", "The plan freeze includes the promise time and the zone. Dispatch does not invent a slot after cooking has started."),
        ("Wrong-meal notes were written as quality complaints. Most were plan changes accepted after the cook started.", "A change after 18:00 is a next-day order. It is not a defect and it is not cooked."),
        ("Leadership, kitchen, and dispatch each had an on-time percentage. The meetings compared different rows.", "On-time means arrived at or before the promised time, full quantity, trusted rows only."),
        ("The cheapest protein quote had the longest lead time and the weakest delivery history.", "Total cost adds freight, a reject penalty, and the carrying cost of the lead time. Under 93% on-time, the quote is out."),
    ]
    workshops = [
        ("W-01", "2025-06-20", "Dispatch, kitchen, founder", "Split the outer-zone breakfast route. Kukatpally and Manikonda leave 15 minutes earlier. Core zones do not absorb that delay."),
        ("W-02", "2025-09-12", "Kitchen, procurement, dispatch", "Freeze the automation fields: meal, quantity, zone, promise time, and box type. Anything else stays off the cook sheet."),
        ("W-03", "2025-11-12", "Kitchen and subscriber support", "A meal swap after 18:00 moves to the next cook. Support stops promising the same morning."),
        ("W-04", "2026-02-18", "Procurement and operations", "Award the four ingredients from the total-cost table. A chat price does not reopen a closed quote."),
    ]
    quotes = [
        ("Q01", "Chicken", "Deccan Poultry", 312, 18, 2, 96.5, 400, 1, "Eligible"),
        ("Q02", "Chicken", "Musheerabad Birds", 289, 27, 4, 91.0, 1400, 0, "On-time history under 93%"),
        ("Q03", "Chicken", "Karimnagar Farms", 334, 14, 2, 97.2, 220, 1, "Eligible"),
        ("Q04", "Paneer", "Nizam Dairy", 268, 12, 1, 98.0, 180, 1, "Eligible"),
        ("Q05", "Paneer", "Secunderabad Milk", 251, 22, 3, 94.4, 900, 1, "Eligible"),
        ("Q06", "Paneer", "Ranga Reddy Dairy", 240, 30, 5, 90.1, 1600, 0, "On-time history under 93%"),
        ("Q07", "Millets and rice", "Godavari Grains", 64, 6, 5, 95.8, 300, 1, "Eligible"),
        ("Q08", "Millets and rice", "Warangal Staples", 58, 11, 8, 92.2, 700, 0, "On-time history under 93%"),
        ("Q09", "Millets and rice", "Telangana Harvest", 69, 5, 4, 97.0, 150, 1, "Eligible"),
        ("Q10", "Meal box", "PackRight Hyderabad", 11.5, 0.8, 3, 97.4, 250, 1, "Eligible"),
        ("Q11", "Meal box", "Bowenpally Cartons", 9.8, 1.6, 7, 93.6, 800, 1, "Eligible"),
        ("Q12", "Meal box", "Shamshabad Pack", 9.1, 2.4, 9, 89.0, 1200, 0, "On-time history under 93%"),
    ]
    return initiatives, milestones, risks, lessons, workshops, quotes


def build() -> None:
    rng = random.Random(SEED)
    DATA.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    db_path = DATA / "profitein.sqlite"
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript((SQL / "001_schema.sql").read_text())
    con.executemany("INSERT INTO zones VALUES (?,?,?)", ZONES)
    con.executemany("INSERT INTO meals VALUES (?,?,?,?)", MEALS)

    subscribers = []
    for index in range(1, 161):
        zone = ZONES[(index - 1) % len(ZONES)]
        tier = "Weekly" if index <= 40 else "Monthly"
        subscribers.append(
            (
                f"S{index:04d}",
                f"Subscriber {index:04d}",
                zone[0],
                PLANS[index % 3],
                tier,
            )
        )
    con.executemany("INSERT INTO subscribers VALUES (?,?,?,?,?)", subscribers)

    deliveries = []
    complaints = []
    changes = []
    exceptions = []
    delivery_seq = complaint_seq = change_seq = exception_seq = 0
    rules = [
        ("DQ-01", "Missing promise time"),
        ("DQ-02", "Duplicate delivery fingerprint"),
        ("DQ-03", "Arrival stamp before the cook date"),
        ("DQ-04", "Meal code not on the menu master"),
        ("DQ-05", "Subscriber id not on the plan master"),
    ]

    for month in month_starts(date(2025, 2, 1), date(2026, 3, 1)):
        days = monthrange(month.year, month.month)[1]
        for _ in range(520):
            delivery_seq += 1
            subscriber = rng.choice(subscribers)
            meal = rng.choice(MEALS)
            day = date(month.year, month.month, rng.randint(1, days))
            promised_hour = 8 if meal[2] == "Breakfast" else 13 if meal[2] == "Lunch" else 20
            delivery_id = f"DL{delivery_seq:06d}"
            if rng.random() < 0.075:
                exception_seq += 1
                rule = rng.choice(rules)
                exceptions.append((f"EX{exception_seq:05d}", delivery_id, day.isoformat(), rule[0], rule[1]))
                continue
            zone = next(item for item in ZONES if item[0] == subscriber[2])
            probability = 0.935
            if zone[2] == "Outer" and month.month in (6, 7) and month.year == 2025:
                probability -= 0.14
            if meal[0] in {"ML-04", "ML-03"} and day < date(2025, 11, 12):
                probability -= 0.02
            on_time = rng.random() < probability
            promised_dt = datetime(day.year, day.month, day.day, promised_hour, 0)
            if on_time:
                arrived_dt = promised_dt - timedelta(minutes=rng.choice([0, 10, 15, 25]))
                qty_delivered = 1
            elif rng.random() < 0.8:
                arrived_dt = promised_dt + timedelta(minutes=rng.choice([25, 40, 70, 110]))
                qty_delivered = 1
            else:
                arrived_dt = promised_dt
                qty_delivered = 0
            arrived = arrived_dt.strftime("%Y-%m-%d %H:%M")
            deliveries.append(
                (
                    delivery_id,
                    day.isoformat(),
                    stamp(day, promised_hour, 0),
                    subscriber[0],
                    meal[0],
                    1,
                    meal[3],
                    arrived,
                    qty_delivered,
                )
            )
            reason = None
            if qty_delivered == 0 and rng.random() < 0.7:
                reason = "Missing meal"
            elif not on_time and rng.random() < 0.45:
                reason = "Late delivery"
            wrong_p = 0.045 if day < date(2025, 11, 12) else 0.012
            if reason is None and rng.random() < wrong_p:
                reason = "Wrong meal or macros"
            if reason is None and rng.random() < 0.01:
                reason = "Damaged box"
            if reason:
                complaint_seq += 1
                complaints.append((f"CMP{complaint_seq:05d}", delivery_id, day.isoformat(), reason))
            change_p = 0.09 if day < date(2025, 11, 12) else 0.045
            if rng.random() < change_p:
                change_seq += 1
                changes.append(
                    (
                        f"CH{change_seq:05d}",
                        delivery_id,
                        day.isoformat(),
                        rng.choice(["Meal swap", "Slot change", "Address change", "Skip day"]),
                    )
                )

    con.executemany("INSERT INTO deliveries VALUES (?,?,?,?,?,?,?,?,?)", deliveries)
    con.executemany("INSERT INTO complaints VALUES (?,?,?,?)", complaints)
    con.executemany("INSERT INTO plan_changes VALUES (?,?,?,?)", changes)
    con.executemany("INSERT INTO dq_exceptions VALUES (?,?,?,?,?)", exceptions)
    initiatives, milestones, risks, lessons, workshops, quotes = governance()
    con.executemany("INSERT INTO initiatives VALUES (?,?,?,?,?,?,?,?,?,?)", initiatives)
    con.executemany("INSERT INTO milestones VALUES (?,?,?,?,?,?)", milestones)
    con.executemany("INSERT INTO risks VALUES (?,?,?,?,?,?,?,?)", risks)
    con.executemany(
        "INSERT INTO lessons VALUES (?,?,?)",
        [(f"L-{index:02d}", row[0], row[1]) for index, row in enumerate(lessons, start=1)],
    )
    con.executemany("INSERT INTO workshops VALUES (?,?,?,?)", workshops)
    con.executemany("INSERT INTO quotes VALUES (?,?,?,?,?,?,?,?,?,?)", quotes)
    con.executescript((SQL / "002_views.sql").read_text())
    con.commit()
    write_pack(con)
    con.close()
    print(f"Built {db_path}")


def rows(con, sql):
    cur = con.execute(sql)
    names = [column[0] for column in cur.description]
    return [dict(zip(names, record)) for record in cur.fetchall()]


def table(records):
    if not records:
        return "<p>No rows.</p>"
    columns = list(records[0])
    head = "".join(f"<th>{html.escape(column)}</th>" for column in columns)
    body = []
    for record in records:
        cells = "".join(f"<td>{html.escape(str(record[column]))}</td>" for column in columns)
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def write_pack(con: sqlite3.Connection) -> None:
    headline = rows(
        con,
        """
        SELECT COUNT(*) AS deliveries,
               ROUND(100.0 * AVG(otif_flag), 1) AS otif_pct,
               ROUND(100.0 * AVG(perfect_flag), 1) AS perfect_pct,
               ROUND(100.0 * AVG(complaint_flag), 1) AS complaint_pct,
               ROUND(100.0 * AVG(change_flag), 1) AS change_pct
        FROM vw_perfect
        """,
    )[0]
    trusted = con.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
    rejected = con.execute("SELECT COUNT(*) FROM dq_exceptions").fetchone()[0]
    trusted_share = round(100 * trusted / (trusted + rejected), 1)
    months = rows(
        con,
        """
        SELECT year_month,
               SUM(deliveries) AS deliveries,
               ROUND(SUM(otif_pct * deliveries) / SUM(deliveries), 1) AS otif_pct,
               ROUND(SUM(complaint_pct * deliveries) / SUM(deliveries), 1) AS complaint_pct
        FROM vw_month_zone
        GROUP BY year_month
        ORDER BY year_month
        """,
    )
    outer = rows(
        con,
        """
        SELECT year_month, zone_name, otif_pct, deliveries
        FROM vw_month_zone
        WHERE band = 'Outer' AND year_month IN ('2025-05', '2025-06', '2025-07', '2025-08')
        ORDER BY zone_name, year_month
        """,
    )
    pareto = rows(con, "SELECT reason, complaints, share_pct FROM vw_complaint_pareto")
    risks = rows(
        con,
        "SELECT risk_id, initiative, score, band, owner, status, description, mitigation FROM vw_risk WHERE status != 'Closed' ORDER BY score DESC",
    )
    awards = rows(
        con,
        """
        SELECT material, supplier_name, unit_price_inr, tco_inr, otif_pct, lead_time_days
        FROM vw_tco
        WHERE eligible = 1
          AND tco_inr = (
              SELECT MIN(t.tco_inr) FROM vw_tco t
              WHERE t.material = vw_tco.material AND t.eligible = 1
          )
        ORDER BY material
        """,
    )
    lessons = rows(con, "SELECT finding, standard_change FROM lessons")
    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>PRO'FIT'EIN · delivery KPI pack · March 2026</title>
<style>
  body {{ margin: 0; background: #eef2f6; color: #1b2838; font-family: "Segoe UI", sans-serif; }}
  main {{ max-width: 980px; margin: 24px auto 48px; background: white; padding: 32px 40px 48px; }}
  h1 {{ font-weight: 650; letter-spacing: -0.03em; margin: 0 0 8px; }}
  h2 {{ font-size: 16px; margin: 28px 0 8px; }}
  .meta {{ color: #5c6b7a; font-size: 13px; }}
  .note {{ background: #f4f7fb; border-left: 4px solid #1f4e79; padding: 10px 12px; font-size: 13px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 16px 0; }}
  .kpi {{ background: #f7f9fb; padding: 12px; border-top: 3px solid #1f4e79; }}
  .kpi b {{ display: block; font-size: 24px; }}
  .kpi span {{ font-size: 11px; letter-spacing: .04em; text-transform: uppercase; color: #5c6b7a; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid #e6ebf1; vertical-align: top; }}
  th {{ font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: #5c6b7a; }}
</style>
</head>
<body>
<main>
  <p class="meta">PRO'FIT'EIN · Hyderabad · operations scorecard · February 2025 to March 2026</p>
  <h1>Outer zones slipped in the monsoon. The cook sheet is no longer the argument.</h1>
  <p class="note">Portfolio sample. Subscribers and prices are synthetic. This is not an export from the company database. Quote these computed rates only as the sample.</p>
  <div class="kpis">
    <div class="kpi"><span>On-time, in-full</span><b>{headline["otif_pct"]}%</b></div>
    <div class="kpi"><span>Perfect delivery</span><b>{headline["perfect_pct"]}%</b></div>
    <div class="kpi"><span>Complaint rate</span><b>{headline["complaint_pct"]}%</b></div>
    <div class="kpi"><span>Plan-change rate</span><b>{headline["change_pct"]}%</b></div>
    <div class="kpi"><span>Trusted rows</span><b>{trusted_share}%</b></div>
  </div>
  <p>{headline["deliveries"]:,} trusted deliveries. {rejected:,} source rows failed a quality rule and are excluded. On-time means the box arrived at or before the promised time and the meal was in it.</p>
  <h2>Three decisions for the Monday review</h2>
  <ol>
    <li>Do not open another outer zone until the June 2026 monsoon week has run on the new route split. Risk R-01 is that June 2025 happens again.</li>
    <li>Close the private Sunday spreadsheet. The automation has been the plan of record since 15 October 2025.</li>
    <li>Keep ingredient awards inside the total-cost table. A lower unit price under 93% on-time stays out.</li>
  </ol>
  <h2>On-time by month</h2>
  {table(months)}
  <h2>Outer zones around the 2025 monsoon</h2>
  {table(outer)}
  <h2>Why subscribers wrote in</h2>
  {table(pareto)}
  <h2>Open risks</h2>
  {table(risks)}
  <h2>Ingredient award on total cost</h2>
  <p>Total cost = price + freight + reject penalty + carrying cost of lead time. Reject penalty = ppm / 1,000,000 × 25 × price. Carrying cost = 12% a year. The award is the eligible quote with the lowest total cost, not the lowest unit price.</p>
  {table(awards)}
  <h2>Standards that replaced the one-off fix</h2>
  {table(lessons)}
</main>
</body>
</html>
"""
    (OUT / "profitein_kpi_pack.html").write_text(document)


if __name__ == "__main__":
    build()
