-- =====================================================================
-- CreatorPulse Analytics: Acquisition Funnel Metrics
-- =====================================================================
-- Description: Analytical queries tracking acquisition funnel stages:
--              Impressions -> Engagements -> Referral Clicks -> Purchases -> Repeat Customers.
--              Includes step-by-step drop-off analysis using LAG() window functions,
--              breakdown by creative content type, and breakdown by creator tier.
-- Dialect: SQLite 3.25+ / ANSI SQL:2016 compatible
-- Tables referenced: campaigns, creators, purchases
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Full Funnel Stage Volumes and Step-by-Step Drop-off Percentages
-- Leverages LAG() and FIRST_VALUE() window functions to evaluate
-- stage-to-stage transition rates and cumulative retention from top of funnel.
-- ---------------------------------------------------------------------
WITH raw_metrics AS (
    SELECT
        (SELECT SUM(impressions) FROM campaigns) AS impressions,
        (SELECT SUM(engagements) FROM campaigns) AS engagements,
        (SELECT SUM(referral_clicks) FROM campaigns) AS referral_clicks,
        (SELECT COUNT(DISTINCT order_id) FROM purchases) AS purchases,
        (SELECT COUNT(*) FROM (
            SELECT customer_id 
            FROM purchases 
            GROUP BY customer_id 
            HAVING COUNT(DISTINCT order_id) >= 2
        )) AS repeat_customers
),
funnel_stages AS (
    SELECT 1 AS stage_id, '1. Impressions' AS stage_name, impressions AS volume FROM raw_metrics
    UNION ALL
    SELECT 2 AS stage_id, '2. Engagements' AS stage_name, engagements AS volume FROM raw_metrics
    UNION ALL
    SELECT 3 AS stage_id, '3. Referral Clicks' AS stage_name, referral_clicks AS volume FROM raw_metrics
    UNION ALL
    SELECT 4 AS stage_id, '4. Purchases' AS stage_name, purchases AS volume FROM raw_metrics
    UNION ALL
    SELECT 5 AS stage_id, '5. Repeat Customers' AS stage_name, repeat_customers AS volume FROM raw_metrics
)
SELECT
    stage_id,
    stage_name,
    volume,
    LAG(volume) OVER (ORDER BY stage_id) AS prev_stage_volume,
    ROUND(volume * 100.0 / NULLIF(LAG(volume) OVER (ORDER BY stage_id), 0), 2) AS conversion_from_prev_pct,
    ROUND((LAG(volume) OVER (ORDER BY stage_id) - volume) * 100.0 / NULLIF(LAG(volume) OVER (ORDER BY stage_id), 0), 2) AS drop_off_pct,
    ROUND(volume * 100.0 / NULLIF(FIRST_VALUE(volume) OVER (ORDER BY stage_id), 0), 4) AS retention_from_top_pct
FROM funnel_stages
ORDER BY stage_id;


-- ---------------------------------------------------------------------
-- 2. Stage-to-Stage Attrition and Bottleneck Identification
-- Pinpoints where the largest absolute and percentage volume losses occur
-- along the acquisition pathway.
-- ---------------------------------------------------------------------
WITH step_volumes AS (
    SELECT
        SUM(impressions) AS total_impressions,
        SUM(engagements) AS total_engagements,
        SUM(referral_clicks) AS total_clicks,
        (SELECT COUNT(DISTINCT order_id) FROM purchases) AS total_orders,
        (SELECT COUNT(*) FROM (
            SELECT customer_id FROM purchases GROUP BY customer_id HAVING COUNT(DISTINCT order_id) >= 2
        )) AS repeat_customers
    FROM campaigns
)
SELECT
    'Impressions -> Engagements' AS funnel_transition,
    total_impressions AS upper_stage_volume,
    total_engagements AS lower_stage_volume,
    (total_impressions - total_engagements) AS absolute_drop_off,
    ROUND((total_impressions - total_engagements) * 100.0 / NULLIF(total_impressions, 0), 2) AS drop_off_rate_pct
FROM step_volumes
UNION ALL
SELECT
    'Engagements -> Referral Clicks' AS funnel_transition,
    total_engagements AS upper_stage_volume,
    total_clicks AS lower_stage_volume,
    (total_engagements - total_clicks) AS absolute_drop_off,
    ROUND((total_engagements - total_clicks) * 100.0 / NULLIF(total_engagements, 0), 2) AS drop_off_rate_pct
FROM step_volumes
UNION ALL
SELECT
    'Referral Clicks -> Purchases' AS funnel_transition,
    total_clicks AS upper_stage_volume,
    total_orders AS lower_stage_volume,
    (total_clicks - total_orders) AS absolute_drop_off,
    ROUND((total_clicks - total_orders) * 100.0 / NULLIF(total_clicks, 0), 2) AS drop_off_rate_pct
FROM step_volumes
UNION ALL
SELECT
    'Purchases -> Repeat Customers' AS funnel_transition,
    total_orders AS upper_stage_volume,
    repeat_customers AS lower_stage_volume,
    (total_orders - repeat_customers) AS absolute_drop_off,
    ROUND((total_orders - repeat_customers) * 100.0 / NULLIF(total_orders, 0), 2) AS drop_off_rate_pct
FROM step_volumes;


-- ---------------------------------------------------------------------
-- 3. Acquisition Funnel by Creative Content Type
-- Compares funnel velocity and conversion depth across content formats
-- (Review, Tutorial, Unboxing, Lifestyle, Discount, etc.).
-- ---------------------------------------------------------------------
WITH content_campaign_metrics AS (
    SELECT
        content_type,
        SUM(impressions) AS impressions,
        SUM(engagements) AS engagements,
        SUM(referral_clicks) AS referral_clicks
    FROM campaigns
    GROUP BY content_type
),
content_purchase_metrics AS (
    SELECT
        cam.content_type,
        COUNT(DISTINCT p.order_id) AS purchases,
        COUNT(DISTINCT p.customer_id) AS unique_customers,
        SUM(CASE WHEN cust_orders.order_count >= 2 THEN 1 ELSE 0 END) AS repeat_customers
    FROM campaigns cam
    JOIN purchases p ON cam.campaign_id = p.campaign_id
    JOIN (
        SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
        FROM purchases
        GROUP BY customer_id
    ) cust_orders ON p.customer_id = cust_orders.customer_id
    GROUP BY cam.content_type
)
SELECT
    ccm.content_type,
    ccm.impressions,
    ccm.engagements,
    ccm.referral_clicks,
    COALESCE(cpm.purchases, 0) AS purchases,
    COALESCE(cpm.unique_customers, 0) AS unique_customers,
    COALESCE(cpm.repeat_customers, 0) AS repeat_customers,
    -- Stage Conversion Rates
    ROUND(ccm.engagements * 100.0 / NULLIF(ccm.impressions, 0), 2) AS impression_to_eng_pct,
    ROUND(ccm.referral_clicks * 100.0 / NULLIF(ccm.engagements, 0), 2) AS eng_to_click_pct,
    ROUND(COALESCE(cpm.purchases, 0) * 100.0 / NULLIF(ccm.referral_clicks, 0), 2) AS click_to_purchase_pct,
    ROUND(COALESCE(cpm.repeat_customers, 0) * 100.0 / NULLIF(cpm.unique_customers, 0), 2) AS repeat_customer_pct
FROM content_campaign_metrics ccm
LEFT JOIN content_purchase_metrics cpm ON ccm.content_type = cpm.content_type
ORDER BY purchases DESC;


-- ---------------------------------------------------------------------
-- 4. Acquisition Funnel by Creator Tier
-- Evaluates audience progression across tiers:
-- Nano (<10K), Micro (10K-100K), Mid-Tier (100K-500K), Macro (500K-1M), Mega (>1M).
-- ---------------------------------------------------------------------
WITH tier_campaign_metrics AS (
    SELECT
        c.creator_tier,
        SUM(cam.impressions) AS impressions,
        SUM(cam.engagements) AS engagements,
        SUM(cam.referral_clicks) AS referral_clicks
    FROM creators c
    LEFT JOIN campaigns cam ON c.creator_id = cam.creator_id
    GROUP BY c.creator_tier
),
tier_purchase_metrics AS (
    SELECT
        c.creator_tier,
        COUNT(DISTINCT p.order_id) AS purchases,
        COUNT(DISTINCT p.customer_id) AS unique_customers
    FROM creators c
    LEFT JOIN purchases p ON c.creator_id = p.creator_id
    GROUP BY c.creator_tier
),
tier_repeat_metrics AS (
    SELECT
        c.creator_tier,
        COUNT(DISTINCT p.customer_id) AS repeat_customers
    FROM creators c
    JOIN purchases p ON c.creator_id = p.creator_id
    WHERE p.customer_id IN (
        SELECT customer_id 
        FROM purchases 
        GROUP BY customer_id 
        HAVING COUNT(DISTINCT order_id) >= 2
    )
    GROUP BY c.creator_tier
)
SELECT
    tcm.creator_tier,
    COALESCE(tcm.impressions, 0) AS impressions,
    COALESCE(tcm.engagements, 0) AS engagements,
    COALESCE(tcm.referral_clicks, 0) AS referral_clicks,
    COALESCE(tpm.purchases, 0) AS purchases,
    COALESCE(tpm.unique_customers, 0) AS unique_customers,
    COALESCE(trm.repeat_customers, 0) AS repeat_customers,
    -- Step Conversion Rates
    ROUND(COALESCE(tcm.engagements, 0) * 100.0 / NULLIF(tcm.impressions, 0), 2) AS engagement_rate,
    ROUND(COALESCE(tcm.referral_clicks, 0) * 100.0 / NULLIF(tcm.impressions, 0), 2) AS ctr,
    ROUND(COALESCE(tpm.purchases, 0) * 100.0 / NULLIF(tcm.referral_clicks, 0), 2) AS conversion_rate,
    ROUND(COALESCE(trm.repeat_customers, 0) * 100.0 / NULLIF(tpm.unique_customers, 0), 2) AS repeat_rate_pct
FROM tier_campaign_metrics tcm
LEFT JOIN tier_purchase_metrics tpm ON tcm.creator_tier = tpm.creator_tier
LEFT JOIN tier_repeat_metrics trm ON tcm.creator_tier = trm.creator_tier
ORDER BY purchases DESC;
