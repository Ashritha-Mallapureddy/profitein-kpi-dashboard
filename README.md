# PRO'FIT'EIN · Hyderabad delivery KPI dashboard

**Open the dashboard:** [ashritha-mallapureddy.github.io/profitein-kpi-dashboard](https://ashritha-mallapureddy.github.io/profitein-kpi-dashboard/)

Portfolio sample for the **Operations & Supply Chain Manager** role at PRO'FIT'EIN, Hyderabad (February 2025 – March 2026).

The business in this model is the meal-subscription operation: a central kitchen, Hyderabad delivery zones, subscriber plan changes, and ingredient buying. Subscribers, meals, and supplier quotes are synthetic. This is not an export from the company's database, and it is not a Power BI file taken from their tenant.

## What the CV bullet looks like in the sample

| CV bullet | Where it is |
| --- | --- |
| Power BI KPI dashboards and SQL reports as one source of truth | `sql/002_views.sql` defines on-time, perfect delivery, complaint rate, and plan-change rate. `app.py` is the dashboard. `output/profitein_kpi_pack.html` is the leadership pack. |
| Data-quality rules before a number is trusted | `dq_exceptions`. Five rules. The scorecard never reads those rows. |
| Automation rollout owned end to end | Initiative `INI-01`, milestones from the current-state map through retirement of the spreadsheet on 15 October 2025. |
| Meetings and workshops that resolve a blocker | `workshops`. Each row is a decision, not an agenda. |
| Lessons learned turned into a standard | `lessons`. |
| RFQ work that protects on-time delivery | `vw_tco`. Price + freight + reject penalty + lead-time carrying cost. Under 93% on-time, the quote is out. |

## Definitions

- **On-time, in-full.** Arrived at or before the promised time, and the meal was delivered.
- **Perfect delivery.** On-time in-full, no complaint, no plan change.
- **Complaint rate.** Trusted deliveries with at least one complaint, divided by trusted deliveries.
- **Risk score.** Probability × impact, each 1 to 5. 15 or higher is high.

In a German PMO review the same four ideas are Liefertreue, perfekte Zustellung, Reklamationsquote, and Risikowert.

## Run

```bash
cd profitein-kpi-dashboard
python src/build_profitein.py
python -m streamlit run app.py
```

Open `output/profitein_kpi_pack.html` if you only need the pack. The seed is fixed.

To rebuild the same model in Power BI Desktop, load the tables from the SQLite file, use the relationships named in the schema, and copy the ratios from `sql/002_views.sql`. If a visual disagrees with `vw_perfect`, the visual is wrong.
