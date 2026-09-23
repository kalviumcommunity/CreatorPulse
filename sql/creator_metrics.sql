-- =====================================================================
-- CreatorPulse Analytics: Creator Performance Metrics
-- =====================================================================
-- Description: Analytical SQL queries evaluating creator revenue contribution,
--              engagement-to-conversion efficiency, customer repeat rates,
--              and historical revenue trends using window functions.
-- Dialect: SQLite 3.25+ / ANSI SQL:2016 compatible
-- Tables referenced: creators, campaigns, purchases
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Top Creators by Revenue
-- Aggregates orders, unique customers, total and average revenue per creator.
-- Window function RANK() calculates creator rank based on gross revenue.
-- ---------------------------------------------------------------------
SELECT
    c.creator_id,
    c.creator_name,
    c.followers,
    c.creator_tier,
    COUNT(DISTINCT p.order_id) AS total_orders,
    COUNT(DISTINCT p.customer_id) AS unique_customers,
    SUM(p.order_value) AS total_revenue,
    AVG(p.order_value) AS avg_order_value,
    RANK() OVER (ORDER BY SUM(p.order_value) DESC) AS revenue_rank
FROM creators c
LEFT JOIN purchases p ON c.creator_id = p.creator_id
GROUP BY c.creator_id, c.creator_name, c.followers, c.creator_tier
ORDER BY total_revenue DESC;


-- ---------------------------------------------------------------------
-- 2. Creator Engagement vs Conversion Comparison
-- Evaluates marketing funnel efficiency from audience reach to purchase.
-- Safe division via NULLIF() prevents division-by-zero errors.
-- ---------------------------------------------------------------------
SELECT
    c.creator_id,
    c.creator_name,
    SUM(cam.impressions) AS total_impressions,
    SUM(cam.engagements) AS total_engagements,
    ROUND(SUM(cam.engagements) * 100.0 / NULLIF(SUM(cam.impressions), 0), 2) AS engagement_rate,
    SUM(cam.referral_clicks) AS total_clicks,
    ROUND(SUM(cam.referral_clicks) * 100.0 / NULLIF(SUM(cam.impressions), 0), 2) AS ctr,
    COUNT(DISTINCT p.order_id) AS purchases,
    ROUND(COUNT(DISTINCT p.order_id) * 100.0 / NULLIF(SUM(cam.referral_clicks), 0), 2) AS conversion_rate
FROM creators c
LEFT JOIN campaigns cam ON c.creator_id = cam.creator_id
LEFT JOIN purchases p ON c.creator_id = p.creator_id
GROUP BY c.creator_id, c.creator_name
ORDER BY conversion_rate DESC;


-- ---------------------------------------------------------------------
-- 2b. CTE-Based Robust Version (Prevents Fan-Out Aggregation)
-- Pre-aggregates campaigns and purchases independently before joining
-- to creators, guaranteeing exact metrics when multiple campaigns and
-- purchases exist for a single creator.
-- ---------------------------------------------------------------------
WITH creator_campaign_agg AS (
    SELECT
        creator_id,
        SUM(impressions) AS total_impressions,
        SUM(engagements) AS total_engagements,
        SUM(referral_clicks) AS total_clicks
    FROM campaigns
    GROUP BY creator_id
),
creator_purchase_agg AS (
    SELECT
        creator_id,
        COUNT(DISTINCT order_id) AS purchases,
        COUNT(DISTINCT customer_id) AS unique_customers,
        SUM(order_value) AS total_revenue
    FROM purchases
    GROUP BY creator_id
)
SELECT
    c.creator_id,
    c.creator_name,
    c.creator_tier,
    COALESCE(cca.total_impressions, 0) AS total_impressions,
    COALESCE(cca.total_engagements, 0) AS total_engagements,
    ROUND(COALESCE(cca.total_engagements, 0) * 100.0 / NULLIF(cca.total_impressions, 0), 2) AS engagement_rate,
    COALESCE(cca.total_clicks, 0) AS total_clicks,
    ROUND(COALESCE(cca.total_clicks, 0) * 100.0 / NULLIF(cca.total_impressions, 0), 2) AS ctr,
    COALESCE(cpa.purchases, 0) AS purchases,
    COALESCE(cpa.total_revenue, 0.0) AS total_revenue,
    ROUND(COALESCE(cpa.purchases, 0) * 100.0 / NULLIF(cca.total_clicks, 0), 2) AS conversion_rate
FROM creators c
LEFT JOIN creator_campaign_agg cca ON c.creator_id = cca.creator_id
LEFT JOIN creator_purchase_agg cpa ON c.creator_id = cpa.creator_id
ORDER BY total_revenue DESC;


-- ---------------------------------------------------------------------
-- 3. Creator Repeat Purchase Analysis
-- Analyzes repeat customer behavior at the creator level.
-- Identifies customer order frequency, total customer spend, and date span.
-- ---------------------------------------------------------------------
SELECT
    creator_id,
    customer_id,
    COUNT(*) AS purchase_count,
    SUM(order_value) AS customer_revenue,
    MIN(purchase_date) AS first_purchase,
    MAX(purchase_date) AS last_purchase
FROM purchases
GROUP BY creator_id, customer_id;


-- ---------------------------------------------------------------------
-- 4. Revenue Trend by Creator Using Window Functions
-- Calculates monthly revenue, running cumulative revenue (SUM OVER),
-- and month-over-month previous revenue (LAG OVER) partitioned by creator.
-- ---------------------------------------------------------------------
SELECT
    creator_id,
    strftime('%Y-%m', purchase_date) AS month,
    SUM(order_value) AS monthly_revenue,
    SUM(SUM(order_value)) OVER (
        PARTITION BY creator_id 
        ORDER BY strftime('%Y-%m', purchase_date)
    ) AS cumulative_revenue,
    LAG(SUM(order_value)) OVER (
        PARTITION BY creator_id 
        ORDER BY strftime('%Y-%m', purchase_date)
    ) AS prev_month_revenue
FROM purchases
GROUP BY creator_id, strftime('%Y-%m', purchase_date)
ORDER BY creator_id, month;
