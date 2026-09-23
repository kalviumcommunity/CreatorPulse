# CreatorPulse Data Dictionary

> ⚠️ This data dictionary describes the **DEMO/SYNTHETIC** dataset used for development.
> All data is artificially generated for demonstration purposes.

## Source Tables

### creators.csv — Influencer/Creator Profiles

| Field | Meaning | Type | Business Role |
|-------|---------|------|---------------|
| creator_id | Unique identifier for each creator (C001–C025) | string | Dimension |
| creator_name | Display name of the creator | string | Dimension |
| followers | Number of followers on primary platform | integer | Metric |
| creator_category | Content category (Fashion, Tech, Beauty, Food, Fitness, Lifestyle, Travel, Gaming) | string | Dimension |
| creator_tier | Size classification based on follower count | string | Dimension |

**Creator Tier Thresholds:**
- Nano: < 10,000 followers
- Micro: 10,000–100,000 followers
- Mid-Tier: 100,000–500,000 followers
- Macro: 500,000–1,000,000 followers
- Mega: > 1,000,000 followers

---

### campaigns.csv — Campaign Performance Data

| Field | Meaning | Type | Business Role |
|-------|---------|------|---------------|
| campaign_id | Unique campaign identifier (CAM001–CAM040) | string | Dimension |
| campaign_name | Descriptive campaign name | string | Dimension |
| creator_id | FK → creators table | string | Dimension |
| campaign_start_date | Campaign launch date | date | Temporal |
| campaign_end_date | Campaign end date | date | Temporal |
| content_type | Type of content (Review, Tutorial, Unboxing, Lifestyle, Discount, Giveaway) | string | Dimension |
| platform | Social media platform (Instagram, YouTube, Twitter) | string | Dimension |
| campaign_budget | Campaign spend in INR | float | Revenue |
| impressions | Total content views/reach | integer | Metric |
| likes | Number of likes | integer | Metric |
| comments | Number of comments | integer | Metric |
| shares | Number of shares | integer | Metric |
| saves | Number of saves/bookmarks | integer | Metric |
| engagements | Total engagements (likes+comments+shares+saves) | integer | Metric |
| referral_clicks | Clicks on referral/affiliate links | integer | Metric |
| landing_page_visits | Visits to product landing pages from referral | integer | Metric |

---

### customers.csv — Customer Acquisition Data

| Field | Meaning | Type | Business Role |
|-------|---------|------|---------------|
| customer_id | Unique customer identifier (CUST0001–CUST6000) | string | Entity |
| first_purchase_date | Date of customer's first observed purchase | date | Temporal |
| referring_creator_id | Creator who referred this customer | string | Dimension |
| referring_campaign_id | Campaign through which customer was acquired | string | Dimension |

---

### purchases.csv — Transaction Data

| Field | Meaning | Type | Business Role |
|-------|---------|------|---------------|
| order_id | Unique order identifier (ORD00001–ORD12000) | string | Entity |
| customer_id | FK → customers table | string | Dimension |
| creator_id | Creator associated with this purchase | string | Dimension |
| campaign_id | Campaign associated with this purchase | string | Dimension |
| purchase_date | Date of purchase | date | Temporal |
| order_value | Order amount in INR (negative values = refunds) | float | Revenue |
| product_id | Product purchased (PROD01–PROD50) | string | Dimension |

---

## Data Relationships

```
creators ─── 1:N ──→ campaigns
creators ─── 1:N ──→ customers (referring_creator_id)
campaigns ── 1:N ──→ customers (referring_campaign_id)  
campaigns ── 1:N ──→ purchases
customers ── 1:N ──→ purchases
```
