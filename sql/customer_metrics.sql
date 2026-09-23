-- =====================================================================
-- CreatorPulse Analytics: Customer Lifecycle & Value Metrics
-- =====================================================================
-- Description: Analytical queries evaluating customer purchase sequence,
--              first vs subsequent purchase behavior, behavioral segmentation
--              (one-time, repeat, high-value), observed Customer Lifetime Value (CLV),
--              30-day repeat purchase velocity, and monthly cohort retention.
-- Dialect: SQLite 3.25+ / ANSI SQL:2016 compatible
-- Tables referenced: purchases, customers, creators, campaigns
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Customer Purchase Sequence & Frequency Using ROW_NUMBER()
-- Sequentially numbers every transaction per customer by purchase date.
-- Computes total customer transaction count and cumulative spend over time.
-- ---------------------------------------------------------------------
SELECT
    order_id,
    customer_id,
    creator_id,
    campaign_id,
    purchase_date,
    order_value,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id 
        ORDER BY purchase_date, order_id
    ) AS purchase_sequence,
    COUNT(*) OVER (
        PARTITION BY customer_id
    ) AS total_customer_orders,
    SUM(order_value) OVER (
        PARTITION BY customer_id 
        ORDER BY purchase_date, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_customer_spend
FROM purchases
ORDER BY customer_id, purchase_sequence;


-- ---------------------------------------------------------------------
-- 2. First vs Subsequent Purchase Identification & Comparison
-- Classifies every order as either initial acquisition or repeat order.
-- Aggregates macro KPIs (orders, revenue, AOV) across purchase types.
-- ---------------------------------------------------------------------
WITH sequenced_purchases AS (
    SELECT
        order_id,
        customer_id,
        order_value,
        purchase_date,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id 
            ORDER BY purchase_date, order_id
        ) AS purchase_seq
    FROM purchases
),
classified_purchases AS (
    SELECT
        order_id,
        customer_id,
        order_value,
        purchase_date,
        CASE 
            WHEN purchase_seq = 1 THEN 'First Purchase'
            ELSE 'Subsequent Purchase'
        END AS purchase_type
    FROM sequenced_purchases
)
SELECT
    purchase_type,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS customer_count,
    SUM(order_value) AS total_revenue,
    ROUND(AVG(order_value), 2) AS avg_order_value,
    ROUND(SUM(order_value) * 100.0 / (SELECT SUM(order_value) FROM purchases), 2) AS revenue_share_pct
FROM classified_purchases
GROUP BY purchase_type;


-- ---------------------------------------------------------------------
-- 3. Customer Behavioral Segmentation (One-Time, Repeat, High-Value)
-- Segments customers based on transaction volume and revenue tier:
-- - One-Time: Exactly 1 purchase
-- - Repeat: 2 or more purchases
-- - High-Value: Top 20% of customer base by observed revenue (NTILE / PERCENT_RANK)
-- ---------------------------------------------------------------------
WITH customer_summary AS (
    SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS order_count,
        SUM(order_value) AS total_spend,
        AVG(order_value) AS avg_order_value,
        MIN(purchase_date) AS first_order_date,
        MAX(purchase_date) AS last_order_date,
        NTILE(5) OVER (ORDER BY SUM(order_value) DESC) AS revenue_quintile
    FROM purchases
    GROUP BY customer_id
)
SELECT
    customer_id,
    order_count,
    total_spend,
    ROUND(avg_order_value, 2) AS avg_order_value,
    first_order_date,
    last_order_date,
    CASE 
        WHEN revenue_quintile = 1 AND order_count >= 2 THEN 'High-Value Repeat'
        WHEN revenue_quintile = 1 AND order_count = 1 THEN 'High-Value One-Time'
        WHEN order_count >= 2 THEN 'Standard Repeat'
        ELSE 'Standard One-Time'
    END AS customer_segment
FROM customer_summary
ORDER BY total_spend DESC;


-- ---------------------------------------------------------------------
-- 4. Customer Lifetime Value (Observed CLV) Analysis
-- Computes observed historical CLV, active lifespan (in days), and order
-- frequency for every customer in the dataset.
-- ---------------------------------------------------------------------
SELECT
    customer_id,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(order_value) AS observed_clv,
    ROUND(AVG(order_value), 2) AS avg_order_value,
    MIN(purchase_date) AS first_purchase_date,
    MAX(purchase_date) AS last_purchase_date,
    ROUND(
        JULIANDAY(MAX(purchase_date)) - JULIANDAY(MIN(purchase_date)), 1
    ) AS customer_lifespan_days,
    CASE 
        WHEN COUNT(DISTINCT order_id) > 1 THEN 
            ROUND((JULIANDAY(MAX(purchase_date)) - JULIANDAY(MIN(purchase_date))) / (COUNT(DISTINCT order_id) - 1), 1)
        ELSE NULL
    END AS avg_days_between_orders
FROM purchases
GROUP BY customer_id
ORDER BY observed_clv DESC;


-- ---------------------------------------------------------------------
-- 5. 30-Day Repeat Purchase Analysis
-- Evaluates retention speed: calculates the percentage of first-time buyers
-- who execute a second purchase within exactly 30 days of their initial order.
-- ---------------------------------------------------------------------
WITH ordered_customer_purchases AS (
    SELECT
        customer_id,
        order_id,
        purchase_date,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id 
            ORDER BY purchase_date, order_id
        ) AS order_seq
    FROM purchases
),
first_two_orders AS (
    SELECT
        p1.customer_id,
        p1.purchase_date AS first_purchase_date,
        p2.purchase_date AS second_purchase_date,
        ROUND(JULIANDAY(p2.purchase_date) - JULIANDAY(p1.purchase_date), 1) AS days_to_second_purchase
    FROM ordered_customer_purchases p1
    LEFT JOIN ordered_customer_purchases p2 
        ON p1.customer_id = p2.customer_id 
        AND p2.order_seq = 2
    WHERE p1.order_seq = 1
)
SELECT
    COUNT(*) AS total_acquired_customers,
    COUNT(second_purchase_date) AS total_repeat_customers,
    SUM(CASE WHEN days_to_second_purchase <= 30.0 THEN 1 ELSE 0 END) AS repeat_within_30_days,
    ROUND(
        SUM(CASE WHEN days_to_second_purchase <= 30.0 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2
    ) AS repeat_rate_30d_pct,
    ROUND(
        COUNT(second_purchase_date) * 100.0 / NULLIF(COUNT(*), 0), 2
    ) AS overall_repeat_rate_pct,
    ROUND(AVG(CASE WHEN days_to_second_purchase <= 30.0 THEN days_to_second_purchase END), 1) AS avg_days_to_repeat_30d
FROM first_two_orders;


-- ---------------------------------------------------------------------
-- 6. Cohort Analysis by First Purchase Month
-- Groups customers by acquisition cohort (Month 0) and tracks retained
-- purchasing activity in subsequent calendar months (Month 0, Month 1, Month 2...).
-- ---------------------------------------------------------------------
WITH customer_cohort AS (
    SELECT
        customer_id,
        strftime('%Y-%m', MIN(purchase_date)) AS cohort_month,
        MIN(purchase_date) AS first_purchase_date
    FROM purchases
    GROUP BY customer_id
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_customer_count
    FROM customer_cohort
    GROUP BY cohort_month
),
customer_activities AS (
    SELECT
        p.customer_id,
        cc.cohort_month,
        -- Month index calculation (offset from cohort month)
        (
            (CAST(strftime('%Y', p.purchase_date) AS INTEGER) - CAST(strftime('%Y', cc.first_purchase_date) AS INTEGER)) * 12 +
            (CAST(strftime('%m', p.purchase_date) AS INTEGER) - CAST(strftime('%m', cc.first_purchase_date) AS INTEGER))
        ) AS month_number
    FROM purchases p
    JOIN customer_cohort cc ON p.customer_id = cc.customer_id
)
SELECT
    ca.cohort_month,
    cs.cohort_customer_count AS cohort_size,
    ca.month_number,
    COUNT(DISTINCT ca.customer_id) AS active_customers,
    ROUND(
        COUNT(DISTINCT ca.customer_id) * 100.0 / NULLIF(cs.cohort_customer_count, 0), 2
    ) AS retention_rate_pct
FROM customer_activities ca
JOIN cohort_sizes cs ON ca.cohort_month = cs.cohort_month
GROUP BY ca.cohort_month, cs.cohort_customer_count, ca.month_number
ORDER BY ca.cohort_month, ca.month_number;
