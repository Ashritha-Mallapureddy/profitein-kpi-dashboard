-- PRO'FIT'EIN portfolio sample. Synthetic subscribers, meals, and suppliers.
-- Trusted deliveries and rejected rows are stored apart, so the scorecard has one population.

CREATE TABLE zones (
    zone_id TEXT PRIMARY KEY,
    zone_name TEXT NOT NULL,
    band TEXT NOT NULL
);

CREATE TABLE meals (
    meal_id TEXT PRIMARY KEY,
    meal_name TEXT NOT NULL,
    meal_family TEXT NOT NULL,
    price_inr REAL NOT NULL
);

CREATE TABLE subscribers (
    subscriber_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    zone_id TEXT NOT NULL REFERENCES zones(zone_id),
    plan_name TEXT NOT NULL,
    tier TEXT NOT NULL
);

CREATE TABLE deliveries (
    delivery_id TEXT PRIMARY KEY,
    delivery_date TEXT NOT NULL,
    promised_by TEXT NOT NULL,
    subscriber_id TEXT NOT NULL REFERENCES subscribers(subscriber_id),
    meal_id TEXT NOT NULL REFERENCES meals(meal_id),
    qty INTEGER NOT NULL,
    net_value_inr REAL NOT NULL,
    arrived_at TEXT NOT NULL,
    qty_delivered INTEGER NOT NULL
);

CREATE TABLE complaints (
    complaint_id TEXT PRIMARY KEY,
    delivery_id TEXT NOT NULL REFERENCES deliveries(delivery_id),
    opened_date TEXT NOT NULL,
    reason TEXT NOT NULL
);

CREATE TABLE plan_changes (
    change_id TEXT PRIMARY KEY,
    delivery_id TEXT NOT NULL REFERENCES deliveries(delivery_id),
    change_date TEXT NOT NULL,
    change_type TEXT NOT NULL
);

CREATE TABLE dq_exceptions (
    exception_id TEXT PRIMARY KEY,
    source_ref TEXT NOT NULL,
    detected_date TEXT NOT NULL,
    rule_code TEXT NOT NULL,
    rule_name TEXT NOT NULL
);

CREATE TABLE initiatives (
    initiative_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    objective TEXT NOT NULL,
    sponsor TEXT NOT NULL,
    owner TEXT NOT NULL,
    rag TEXT NOT NULL,
    start_date TEXT NOT NULL,
    target_date TEXT NOT NULL,
    kpi TEXT NOT NULL,
    status_note TEXT NOT NULL
);

CREATE TABLE milestones (
    milestone_id TEXT PRIMARY KEY,
    initiative_id TEXT NOT NULL REFERENCES initiatives(initiative_id),
    name TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL,
    owner TEXT NOT NULL
);

CREATE TABLE risks (
    risk_id TEXT PRIMARY KEY,
    initiative_id TEXT NOT NULL REFERENCES initiatives(initiative_id),
    description TEXT NOT NULL,
    probability INTEGER NOT NULL,
    impact INTEGER NOT NULL,
    mitigation TEXT NOT NULL,
    owner TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE lessons (
    lesson_id TEXT PRIMARY KEY,
    finding TEXT NOT NULL,
    standard_change TEXT NOT NULL
);

CREATE TABLE workshops (
    workshop_id TEXT PRIMARY KEY,
    held_on TEXT NOT NULL,
    audience TEXT NOT NULL,
    decision TEXT NOT NULL
);

CREATE TABLE quotes (
    quote_id TEXT PRIMARY KEY,
    material TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    unit_price_inr REAL NOT NULL,
    freight_per_unit REAL NOT NULL,
    lead_time_days INTEGER NOT NULL,
    otif_pct REAL NOT NULL,
    ppm INTEGER NOT NULL,
    eligible INTEGER NOT NULL,
    eligibility_note TEXT NOT NULL
);
