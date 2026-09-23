import os
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_demo_data():
    os.makedirs('data/demo', exist_ok=True)
    
    np.random.seed(42)
    random.seed(42)

    # 1. Creators (25 rows)
    creator_ids = [f"C{str(i).zfill(3)}" for i in range(1, 26)]
    indian_names = [
        "Aarav Patel", "Vihaan Sharma", "Vivaan Singh", "Ananya Gupta", "Diya Kumar", 
        "Ishaan Desai", "Aditya Reddy", "Saanvi Joshi", "Nisha Mehta", "Arjun Nair", 
        "Rohan Bhatia", "Neha Iyer", "Rahul Rao", "Priya Chatterjee", "Kabir Das", 
        "Anushka Verma", "Sneha Kapoor", "Kavya Menon", "Aarohi Nambiar", "Aryan Pillai",
        "Maya Saxena", "Riya Ahuja", "Dev Tiwari", "Zara Khan", "Aisha Sheikh"
    ]
    categories = ["Fashion", "Tech", "Beauty", "Food", "Fitness", "Lifestyle", "Travel", "Gaming"]

    creators_data = []
    for cid, name in zip(creator_ids, indian_names):
        followers = int(np.random.lognormal(mean=11.5, sigma=1.5))
        followers = max(1000, min(followers, 2000000))
        
        if followers < 10000:
            tier = "Nano"
        elif followers <= 100000:
            tier = "Micro"
        elif followers <= 500000:
            tier = "Mid-Tier"
        elif followers <= 1000000:
            tier = "Macro"
        else:
            tier = "Mega"
            
        creators_data.append({
            "creator_id": cid,
            "creator_name": name,
            "followers": followers,
            "creator_category": random.choice(categories),
            "creator_tier": tier
        })

    creators_df = pd.DataFrame(creators_data)

    # 2. Campaigns (40 rows)
    campaign_ids = [f"CAM{str(i).zfill(3)}" for i in range(1, 41)]
    content_types = ["Review", "Tutorial", "Unboxing", "Lifestyle", "Discount", "Giveaway"]
    platforms = ["Instagram", "YouTube", "Twitter"]

    campaigns_data = []
    start_date_base = datetime(2026, 1, 1)
    end_date_base = datetime(2026, 6, 30)
    days_between = (end_date_base - start_date_base).days

    for cid in campaign_ids:
        creator = creators_df.sample(1).iloc[0]
        ctype = random.choice(content_types)
        
        start_offset = random.randint(0, days_between - 30)
        start_date = start_date_base + timedelta(days=start_offset)
        duration = random.randint(7, 30)
        end_date = start_date + timedelta(days=duration)
        
        budget = int(np.random.uniform(5000, 500000))
        
        impression_rate = np.random.uniform(0.1, 0.4)
        impressions = int(creator['followers'] * impression_rate)
        
        er = np.random.uniform(0.02, 0.12)
        engagements = int(impressions * er)
        
        likes = int(engagements * np.random.uniform(0.7, 0.85))
        comments = int(engagements * np.random.uniform(0.05, 0.15))
        shares = int(engagements * np.random.uniform(0.02, 0.10))
        saves = engagements - (likes + comments + shares)
        
        ctr_base = np.random.uniform(0.01, 0.08)
        if ctype in ["Review", "Tutorial"]:
            ctr_base *= 1.2
        elif ctype == "Discount":
            ctr_base *= 1.5
        elif ctype == "Giveaway":
            ctr_base *= 0.8
            
        referral_clicks = int(engagements * ctr_base)
        landing_page_visits = int(referral_clicks * np.random.uniform(0.7, 0.9))
        
        campaigns_data.append({
            "campaign_id": cid,
            "campaign_name": f"{creator['creator_category']} {ctype} {start_date.strftime('%b')}",
            "creator_id": creator['creator_id'],
            "campaign_start_date": start_date.strftime("%Y-%m-%d"),
            "campaign_end_date": end_date.strftime("%Y-%m-%d"),
            "content_type": ctype,
            "platform": random.choice(platforms),
            "campaign_budget": budget,
            "impressions": impressions,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "engagements": engagements,
            "referral_clicks": referral_clicks,
            "landing_page_visits": landing_page_visits
        })

    campaigns_df = pd.DataFrame(campaigns_data)

    mask = np.random.rand(len(campaigns_df)) < 0.025
    campaigns_df.loc[mask, 'referral_clicks'] = np.nan

    mask2 = np.random.rand(len(campaigns_df)) < 0.01
    campaigns_df.loc[mask2, 'comments'] = np.nan

    # 3. Customers (6000) & 4. Purchases (12000)
    customer_ids = [f"CUST{str(i).zfill(4)}" for i in range(1, 6001)]
    customers_data = []
    purchases_data = []

    product_ids = [f"PROD{str(i).zfill(2)}" for i in range(1, 51)]
    order_id_counter = 1

    creator_archetypes = {}
    for cid in creators_df['creator_id']:
        archetype = np.random.choice([0, 1, 2, 3], p=[0.4, 0.2, 0.2, 0.2])
        creator_archetypes[cid] = archetype

    for cust_id in customer_ids:
        camp = campaigns_df.sample(1).iloc[0]
        camp_id = camp['campaign_id']
        creator_id = camp['creator_id']
        ctype = camp['content_type']
        
        c_start = datetime.strptime(camp['campaign_start_date'], "%Y-%m-%d")
        c_end = datetime.strptime(camp['campaign_end_date'], "%Y-%m-%d")
        
        first_purchase_offset = random.randint(0, (c_end - c_start).days)
        first_purchase_date = c_start + timedelta(days=first_purchase_offset)
        
        customers_data.append({
            "customer_id": cust_id,
            "first_purchase_date": first_purchase_date.strftime("%Y-%m-%d"),
            "referring_creator_id": creator_id,
            "referring_campaign_id": camp_id
        })
        
        arch = creator_archetypes[creator_id]
        
        repeat_prob = 0.32
        if arch == 2:
            repeat_prob += 0.15
        elif arch == 3 or ctype == "Discount":
            repeat_prob -= 0.15
            
        num_purchases = 1
        if random.random() < repeat_prob:
            num_purchases += np.random.poisson(1.5)
            num_purchases = min(max(2, num_purchases), 10)
            
        current_date = first_purchase_date
        for _ in range(int(num_purchases)):
            order_value = int(np.random.gamma(shape=2.0, scale=2000))
            order_value = max(200, min(order_value, 15000))
            
            purchases_data.append({
                "order_id": f"ORD{str(order_id_counter).zfill(5)}",
                "customer_id": cust_id,
                "creator_id": creator_id,
                "campaign_id": camp_id,
                "purchase_date": current_date.strftime("%Y-%m-%d"),
                "order_value": order_value,
                "product_id": random.choice(product_ids)
            })
            order_id_counter += 1
            
            current_date += timedelta(days=random.randint(5, 60))

    purchases_df = pd.DataFrame(purchases_data)

    if len(purchases_df) > 12000:
        purchases_df = purchases_df.sample(n=12000).reset_index(drop=True)
    elif len(purchases_df) < 12000:
        extra = purchases_df.sample(n=12000 - len(purchases_df), replace=True)
        purchases_df = pd.concat([purchases_df, extra], ignore_index=True)
        
    duplicates = purchases_df.sample(frac=0.003)
    purchases_df = pd.concat([purchases_df, duplicates], ignore_index=True)
    
    # 3-5 negative order values
    neg_idx = np.random.choice(purchases_df.index, size=random.randint(3, 5), replace=False)
    purchases_df.loc[neg_idx, 'order_value'] = -purchases_df.loc[neg_idx, 'order_value'].abs()

    creators_df.to_csv("data/demo/creators.csv", index=False)
    campaigns_df.to_csv("data/demo/campaigns.csv", index=False)
    pd.DataFrame(customers_data).to_csv("data/demo/customers.csv", index=False)
    purchases_df.to_csv("data/demo/purchases.csv", index=False)

    print("Data generation complete. Checking row counts:")
    print(f"Creators: {len(creators_df)}")
    print(f"Campaigns: {len(campaigns_df)}")
    print(f"Customers: {len(customers_data)}")
    print(f"Purchases: {len(purchases_df)}")

if __name__ == "__main__":
    generate_demo_data()
