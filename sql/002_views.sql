-- On-time, in-full: arrived at or before the promised time, full quantity.
-- Perfect delivery: on-time in-full, no complaint, no plan change.

CREATE VIEW vw_delivery AS
SELECT
    d.delivery_id,
    d.delivery_date,
    substr(d.delivery_date, 1, 7) AS year_month,
    d.promised_by,
    d.qty,
    d.qty_delivered,
    d.net_value_inr,
    d.arrived_at,
    s.subscriber_id,
    s.display_name,
    s.plan_name,
    s.tier,
    z.zone_id,
    z.zone_name,
    z.band,
    m.meal_id,
    m.meal_name,
    m.meal_family,
    CASE
        WHEN d.arrived_at <= d.promised_by AND d.qty_delivered >= d.qty THEN 1
        ELSE 0
    END AS otif_flag,
    CASE WHEN c.delivery_id IS NULL THEN 0 ELSE 1 END AS complaint_flag,
    CASE WHEN ch.delivery_id IS NULL THEN 0 ELSE 1 END AS change_flag
FROM deliveries d
JOIN subscribers s ON s.subscriber_id = d.subscriber_id
JOIN zones z ON z.zone_id = s.zone_id
JOIN meals m ON m.meal_id = d.meal_id
LEFT JOIN (SELECT DISTINCT delivery_id FROM complaints) c ON c.delivery_id = d.delivery_id
LEFT JOIN (SELECT DISTINCT delivery_id FROM plan_changes) ch ON ch.delivery_id = d.delivery_id;

CREATE VIEW vw_perfect AS
SELECT
    *,
    CASE WHEN otif_flag = 1 AND complaint_flag = 0 AND change_flag = 0 THEN 1 ELSE 0 END AS perfect_flag
FROM vw_delivery;

CREATE VIEW vw_month_zone AS
SELECT
    year_month,
    zone_name,
    band,
    COUNT(*) AS deliveries,
    ROUND(100.0 * AVG(otif_flag), 1) AS otif_pct,
    ROUND(100.0 * AVG(perfect_flag), 1) AS perfect_pct,
    ROUND(100.0 * AVG(complaint_flag), 1) AS complaint_pct,
    ROUND(100.0 * AVG(change_flag), 1) AS change_pct,
    ROUND(SUM(net_value_inr), 0) AS revenue_inr
FROM vw_perfect
GROUP BY year_month, zone_name, band;

CREATE VIEW vw_complaint_pareto AS
SELECT
    reason,
    COUNT(*) AS complaints,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct
FROM complaints
GROUP BY reason
ORDER BY complaints DESC;

CREATE VIEW vw_risk AS
SELECT
    r.risk_id,
    i.name AS initiative,
    r.description,
    r.probability,
    r.impact,
    r.probability * r.impact AS score,
    CASE
        WHEN r.probability * r.impact >= 15 THEN 'High'
        WHEN r.probability * r.impact >= 8 THEN 'Medium'
        ELSE 'Low'
    END AS band,
    r.mitigation,
    r.owner,
    r.status
FROM risks r
JOIN initiatives i ON i.initiative_id = r.initiative_id;

CREATE VIEW vw_tco AS
SELECT
    material,
    supplier_name,
    unit_price_inr,
    freight_per_unit,
    lead_time_days,
    otif_pct,
    ppm,
    eligible,
    eligibility_note,
    ROUND(
        unit_price_inr
        + freight_per_unit
        + (ppm / 1000000.0) * unit_price_inr * 25
        + unit_price_inr * 0.12 * lead_time_days / 365.0,
        2
    ) AS tco_inr
FROM quotes;
