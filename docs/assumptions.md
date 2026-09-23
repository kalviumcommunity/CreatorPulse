# CreatorPulse — Assumptions

> All assumptions are documented here. These should be reviewed when interpreting results.

## Metric Definitions

1. **Conversion rate denominator is `referral_clicks`**
   - Reason: The dataset does not reliably track individual user journeys. `referral_clicks` represents the top-of-purchase-funnel entry point from creator content.

2. **Repeat purchase = customer with 2+ orders in the purchases table**
   - Reason: This is the simplest observable definition. We count distinct orders per customer_id.

3. **High-value customer = top 20% by total observed revenue**
   - Reason: Data-driven threshold avoids arbitrary fixed values. The 80th percentile of per-customer total spend is used.

4. **Creator tier thresholds are fixed**
   - Nano: < 10,000 followers
   - Micro: 10,000–100,000 followers
   - Mid-Tier: 100,000–500,000 followers
   - Macro: 500,000–1,000,000 followers
   - Mega: > 1,000,000 followers
   - Reason: Industry-standard influencer tier classification.

## Data Handling

5. **Missing `referral_clicks` are excluded from CTR and conversion calculations**
   - Reason: Assuming 0 clicks would artificially inflate denominators and distort rates. Missing ≠ zero.

6. **Negative `order_value` is treated as refunds**
   - Reason: Negative monetary values in purchase data typically represent returns or refunds. These are flagged (`is_refund = True`) but not removed from the dataset to preserve audit trail.

7. **Negative `saves` values are clamped to 0**
   - Reason: Saves cannot logically be negative. These appear to be data quality errors and are corrected during cleaning.

## Analytical Scope

8. **All findings are observational, not causal**
   - Reason: This is cross-sectional observational data. Correlation does not imply causation. No experimental design (A/B testing) is used.

9. **Demo/synthetic data — not real business findings**
   - Reason: No real dataset was provided. All data is generated synthetically with realistic but artificial relationships.

10. **Engagement rate is recomputed from atomic columns**
    - Formula: `(likes + comments + shares + saves) / impressions × 100`
    - Reason: The pre-computed `engagements` column is validated against the sum of individual engagement columns and recalculated during cleaning.

## Temporal

11. **`first_purchase_date` from customers.csv is used for cohort assignment**
    - Reason: This represents the earliest known purchase date for each customer.

12. **Customer segments are mutually exclusive**
    - Priority: High-value > Repeat > One-time
    - A customer in the top 20% by revenue is classified as "High-value" even if they are also a repeat buyer.
