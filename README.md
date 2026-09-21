# CreatorPulse
# Product Requirements Document (PRD): CreatorPulse

## 1. Product Overview
**Product Name:** CreatorPulse
**Tagline:** Sustainable Influencer Acquisition Analytics
**Type:** Interactive Data Analytics Product (Streamlit-based)

### Problem Statement
A social commerce platform captures influencer campaign metrics, referral traffic, and purchase behavior, but marketing teams still cannot determine which creator engagement patterns produce sustainable customer acquisition.

### Product Vision
CreatorPulse analyzes influencer campaign performance, referral traffic, and customer purchase behavior. It transforms raw social-commerce data into actionable insights through a robust pipeline: 
**Data → Cleaning → Validation → Analysis → KPIs → Visualizations → Business Insights**

---

## 2. Target Audience & Stakeholders
**Primary Stakeholder:** Marketing / Growth Team
They need to make data-driven decisions about:
* Creator selection & Campaign allocation
* Content & Referral strategy
* Customer acquisition & Retention
* Campaign effectiveness

---

## 3. Core Business Questions
The entire product must answer one primary question:
> "Which influencer engagement patterns are associated with sustainable customer acquisition, measured through conversion, repeat purchasing, retention, and customer value?"

### Secondary Questions
1. **Creator Performance:** Who generates the most referral traffic, purchases, revenue, and new/repeat customers?
2. **Engagement vs Conversion:** Does higher engagement correspond to higher conversion?
3. **Engagement vs Sustainability:** Does high engagement correspond to sustainable customer acquisition (retention, lifetime value)?
4. **Creator Quality Patterns:** Are there creators with high engagement and first-time purchases but poor repeat purchase behavior?
5. **Content Type Efficacy:** Which content types (Review, Tutorial, Unboxing, etc.) drive the best metrics?
6. **Campaign Performance:** Which campaigns have the highest revenue, lowest CAC, and best repeat purchase rates?
7. **Funnel Performance:** Where do customers drop off in the acquisition funnel?
8. **Time Trends:** How do creator/campaign metrics change over time?

---

## 4. Expected Data Model
The product should work with the following data entities:
1. **Creator / Influencer Data:** `creator_id`, `creator_name`, `followers`, `creator_category`, `creator_tier`
2. **Campaign Data:** `campaign_id`, `campaign_name`, `creator_id`, `start_date`, `end_date`, `content_type`, `platform`, `budget`
3. **Engagement Data:** `impressions`, `likes`, `comments`, `shares`, `saves`, `engagements`
4. **Referral Data:** `referral_clicks`, `landing_page_visits`, `referral_code`
5. **Purchase Data:** `customer_id`, `order_id`, `creator_id`, `campaign_id`, `purchase_date`, `order_value`, `product_id`

*(Note: If no real data is provided, a synthetic DEMO dataset will be generated with 20+ creators, 30+ campaigns, 5,000+ customers, and 10,000+ purchases.)*

---

## 5. Data Pipeline & Quality Requirements
**Data Principle:** NEVER fabricate analytical conclusions. If a metric cannot be calculated due to missing data, explicitly mark it as "Unavailable".

### Pipeline Structure
Raw Data → File Loading → Schema Detection → Dataset Profiling → Data Cleaning → Data Type Standardization → Missing Value Handling → Duplicate Detection → Validation → Multi-source Merge → Feature Engineering → Analytics Dataset → Dashboard

### Data Profiling & Cleaning
* Profile datasets for row/column counts, missing values, duplicates, numeric/date ranges, and outliers.
* Robustly handle missing values (do not blindly replace with zeros).
* Standardize data types (e.g., Dates to `datetime`, IDs to `string`).

---

## 6. Business KPI Definitions
* **Total Revenue:** Sum of valid order values.
* **Unique Customers:** Count distinct customer IDs.
* **New Customers:** Customers making their first observed purchase.
* **Repeat Customers:** Customers with 2+ observed purchases.
* **Repeat Purchase Rate:** Repeat Customers / Unique Customers.
* **Engagement Rate:** (Likes + Comments + Shares + Saves) / Impressions.
* **Click Through Rate (CTR):** Referral Clicks / Impressions.
* **Conversion Rate:** Purchases / Referral Clicks (or Landing Page Visits).
* **Average Order Value (AOV):** Total Revenue / Number of Orders.

---

## 7. Analytical Features
### Exploratory Data Analysis (EDA)
Distribution analysis for Engagement rate, Referral clicks, Conversion rate, Revenue, Order value, and Repeat purchase rate.
### Correlation Analysis
A correlation matrix for numerical variables (with a strict disclaimer: *Correlation indicates association, not causation*).
### Segmentation
* **Customer Segmentation:** One-time Buyer, Repeat Buyer, High-value Buyer.
* **Creator Segmentation:** Data-driven quartiles (Q1-Q4) based on metrics.
### Funnel Analysis
Visualize volume, conversion %, and drop-off % across:
`Impressions → Engagement → Referral Clicks → Product Visits → Purchases → Repeat Purchases`
### Creator Pattern Analysis
Identify trends like "High Engagement + Low Conversion" or "Moderate Engagement + High Repeat Purchase".

---

## 8. Application Architecture & UX
**Platform:** Streamlit (Multipage App using `st.Page` and `st.navigation`)
**Visual Design:** Clean, professional, data-focused. Use semantic colors (Green=Positive, Amber=Warning, Red=Problem). Avoid excessive clutter or animations.

### Proposed Page Structure
1. **Overview (Landing Page):** Executive KPI cards, date/global filters, revenue/purchase trends, acquisition funnel, and high-level engagement scatter plots.
2. **Creator Analysis:** Creator-level metric tables, deep-dive views for individual creator trends, and optional creator comparison.
3. **Campaign Analysis:** Campaign-level metrics and charts (revenue, conversion, engagement).
4. **Customer Behaviour:** Purchase frequency distribution, revenue distribution, and cohort/retention analysis.
5. **Funnel Analysis:** Detailed drop-off metrics filterable by creator, campaign, or date.
6. **Data Quality:** Transparent data engineering summary (missing values, duplicates, invalid records).
7. **Insights:** Deterministic, evidence-based observations generated from the data (e.g., "Creator X shows moderate engagement but high repeat purchase rate").

---

## 9. Non-Functional Requirements
* **Performance:** Use Streamlit caching (`@st.cache_data`) for expensive data-loading and transformations.
* **Code Quality:** Modular architecture. Separate data loading, cleaning, metrics, analytics, visualization, and UI logic.
* **Error Handling:** Graceful fallbacks. The app must never crash due to missing columns or empty filters (display "No records match" or "Metric unavailable" instead).
* **Testing:** Include unit tests for calculations like engagement rate, conversion rate, and missing value handling.
* **SQL Integration:** Use SQL for analytical evidence where appropriate (filtering, aggregation, window functions).
