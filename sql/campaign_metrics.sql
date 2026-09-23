-- =====================================================================
-- CreatorPulse Analytics: Campaign Performance Metrics
-- =====================================================================
-- Description: Analytical queries evaluating marketing campaign performance,
--              financial return on investment (ROI/ROAS), conversion rankings,
--              creative content type comparison, and spend efficiency (CAC, CPC, CPM).
-- Dialect: SQLite 3.25+ / ANSI SQL:2016 compatible
-- Tables referenced: campaigns, creators, purchases
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Campaign Performance with JOIN to Creators and Purchases
-- Aggregates orders, unique customers, and revenue per campaign while
-- linking to creator attributes and campaign metadata.
-- Uses a CTE to prevent Cartesian multiplication of metrics.
-- ---------------------------------------------------------------------
WITH campaign_purchases AS (
    SELECT
        campaign_id,
        COUNT(DISTINCT order_id) AS total_orders,
        COUNT(DISTINCT customer_id) AS unique_customers,
        SUM(order_value) AS total_revenue,
        AVG(order_value) AS avg_order_value
    FROM purchases
    GROUP BY campaign_id
)
SELECT
    cam.campaign_id,
    cam.campaign_name,
    cam.platform,
    cam.content_type,
    c.creator_id,
    c.creator_name,
    c.creator_tier,
    cam.campaign_budget,
    cam.impressions,
    cam.engagements,
    cam.referral_clicks,
    COALESCE(cp.total_orders, 0) AS total_orders,
    COALESCE(cp.unique_customers, 0) AS unique_customers,
    COALESCE(cp.total_revenue, 0.0) AS total_revenue,
    ROUND(COALESCE(cp.avg_order_value, 0.0), 2) AS avg_order_value,
    ROUND(cam.engagements * 100.0 / NULLIF(cam.impressions, 0), 2) AS engagement_rate,
    ROUND(cam.referral_clicks * 100.0 / NULLIF(cam.impressions, 0), 2) AS ctr,
    ROUND(COALESCE(cp.total_orders, 0) * 100.0 / NULLIF(cam.referral_clicks, 0), 2) AS conversion_rate
FROM campaigns cam
JOIN creators c ON cam.creator_id = c.creator_id
LEFT JOIN campaign_purchases cp ON cam.campaign_id = cp.campaign_id
ORDER BY total_revenue DESC;


-- ---------------------------------------------------------------------
-- 2. Campaign ROI and Financial Profitability
-- Evaluates gross revenue against campaign budget.
-- Calculates ROI ratio (Revenue / Budget) and Net ROI percentage.
-- ---------------------------------------------------------------------
WITH campaign_financials AS (
    SELECT
        campaign_id,
        SUM(order_value) AS total_revenue,
        COUNT(DISTINCT order_id) AS orders_count
    FROM purchases
    GROUP BY campaign_id
)
SELECT
    cam.campaign_id,
    cam.campaign_name,
    c.creator_name,
    c.creator_tier,
    cam.campaign_budget,
    COALESCE(cf.total_revenue, 0.0) AS total_revenue,
    COALESCE(cf.orders_count, 0) AS total_orders,
    ROUND(COALESCE(cf.total_revenue, 0.0) / NULLIF(cam.campaign_budget, 0), 2) AS roi_ratio,
    ROUND((COALESCE(cf.total_revenue, 0.0) - cam.campaign_budget) * 100.0 / NULLIF(cam.campaign_budget, 0), 2) AS net_roi_pct,
    CASE 
        WHEN COALESCE(cf.total_revenue, 0.0) >= cam.campaign_budget THEN 'Profitable'
        WHEN COALESCE(cf.total_revenue, 0.0) > 0 THEN 'Partial Recovery'
        ELSE 'Zero Return'
    END AS profitability_status
FROM campaigns cam
JOIN creators c ON cam.creator_id = c.creator_id
LEFT JOIN campaign_financials cf ON cam.campaign_id = cf.campaign_id
ORDER BY roi_ratio DESC;


-- ---------------------------------------------------------------------
-- 3. Campaign Ranking by Conversion Rate
-- Ranks campaigns by conversion rate (orders / referral_clicks) using
-- window functions RANK() and DENSE_RANK().
-- Excludes campaigns with zero referral clicks to maintain statistical validity.
-- ---------------------------------------------------------------------
WITH campaign_order_counts AS (
    SELECT
        campaign_id,
        COUNT(DISTINCT order_id) AS orders
    FROM purchases
    GROUP BY campaign_id
),
campaign_conversions AS (
    SELECT
        cam.campaign_id,
        cam.campaign_name,
        cam.content_type,
        cam.platform,
        c.creator_name,
        cam.referral_clicks,
        COALESCE(coc.orders, 0) AS orders,
        ROUND(COALESCE(coc.orders, 0) * 100.0 / NULLIF(cam.referral_clicks, 0), 2) AS conversion_rate
    FROM campaigns cam
    JOIN creators c ON cam.creator_id = c.creator_id
    LEFT JOIN campaign_order_counts coc ON cam.campaign_id = coc.campaign_id
    WHERE cam.referral_clicks > 0
)
SELECT
    campaign_id,
    campaign_name,
    creator_name,
    platform,
    content_type,
    referral_clicks,
    orders,
    conversion_rate,
    RANK() OVER (ORDER BY conversion_rate DESC) AS conversion_rank,
    DENSE_RANK() OVER (ORDER BY conversion_rate DESC) AS conversion_dense_rank
FROM campaign_conversions
ORDER BY conversion_rank;


-- ---------------------------------------------------------------------
-- 4. Content Type Performance Comparison
-- Aggregates funnel metrics, engagement, and revenue across creative formats
-- (e.g. Review, Tutorial, Unboxing, Lifestyle, Discount, Giveaway).
-- ---------------------------------------------------------------------
WITH content_purchases AS (
    SELECT
        cam.content_type,
        COUNT(DISTINCT cam.campaign_id) AS total_campaigns,
        SUM(cam.campaign_budget) AS total_budget,
        SUM(cam.impressions) AS total_impressions,
        SUM(cam.engagements) AS total_engagements,
        SUM(cam.referral_clicks) AS total_clicks,
        COALESCE(SUM(p.order_value), 0.0) AS total_revenue,
        COUNT(DISTINCT p.order_id) AS total_orders,
        COUNT(DISTINCT p.customer_id) AS total_customers
    FROM campaigns cam
    LEFT JOIN purchases p ON cam.campaign_id = p.campaign_id
    GROUP BY cam.content_type
)
SELECT
    content_type,
    total_campaigns,
    total_budget,
    total_impressions,
    total_engagements,
    total_clicks,
    total_orders,
    total_revenue,
    ROUND(total_engagements * 100.0 / NULLIF(total_impressions, 0), 2) AS avg_engagement_rate,
    ROUND(total_clicks * 100.0 / NULLIF(total_impressions, 0), 2) AS avg_ctr,
    ROUND(total_orders * 100.0 / NULLIF(total_clicks, 0), 2) AS avg_conversion_rate,
    ROUND(total_revenue / NULLIF(total_budget, 0), 2) AS roi_ratio,
    ROUND(total_revenue / NULLIF(total_orders, 0), 2) AS avg_order_value
FROM content_purchases
ORDER BY total_revenue DESC;


-- ---------------------------------------------------------------------
-- 5. Campaign Spend Efficiency & Unit Economics (CAC, CPC, CPE, CPM)
-- Measures cost per unit of acquisition across funnel milestones:
-- CPM (Cost per 1K impressions), CPC (Cost per click),
-- CPE (Cost per engagement), and CAC (Campaign Budget / New Customers Acquired).
-- ---------------------------------------------------------------------
WITH customer_first_purchase AS (
    SELECT
        customer_id,
        MIN(purchase_date) AS first_purchase_date
    FROM purchases
    GROUP BY customer_id
),
campaign_new_customers AS (
    SELECT
        p.campaign_id,
        COUNT(DISTINCT p.customer_id) AS new_customers_acquired
    FROM purchases p
    JOIN customer_first_purchase cfp 
        ON p.customer_id = cfp.customer_id 
        AND p.purchase_date = cfp.first_purchase_date
    GROUP BY p.campaign_id
)
SELECT
    cam.campaign_id,
    cam.campaign_name,
    cam.platform,
    cam.campaign_budget,
    cam.impressions,
    cam.engagements,
    cam.referral_clicks,
    COALESCE(cnc.new_customers_acquired, 0) AS new_customers,
    ROUND(cam.campaign_budget * 1000.0 / NULLIF(cam.impressions, 0), 2) AS cpm,
    ROUND(cam.campaign_budget * 1.0 / NULLIF(cam.engagements, 0), 2) AS cpe,
    ROUND(cam.campaign_budget * 1.0 / NULLIF(cam.referral_clicks, 0), 2) AS cpc,
    ROUND(cam.campaign_budget * 1.0 / NULLIF(cnc.new_customers_acquired, 0), 2) AS cac
FROM campaigns cam
LEFT JOIN campaign_new_customers cnc ON cam.campaign_id = cnc.campaign_id
ORDER BY cac ASC;
