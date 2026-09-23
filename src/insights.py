"""Insights module — Deterministic rule-based insight engine for CreatorPulse.

IMPORTANT: All insights are observational, not causal. The disclaimer is included
in every insight description.
"""
import pandas as pd
from typing import Dict, Any, List
from .utils import safe_divide


DISCLAIMER = "Note: This is an observed pattern in the data, not a causal claim."


def generate_insights(
    data_dict: Dict[str, pd.DataFrame],
    creator_metrics: pd.DataFrame,
    campaign_metrics: pd.DataFrame,
    funnel_metrics: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate deterministic, evidence-based insights from computed analytics.
    
    Each insight contains: id, title, description (with actual metrics), category, severity.
    Rules are applied only when supporting data is available.
    """
    insights = []
    idx = 1

    # --- INSIGHT: High Engagement / Low Conversion ---
    if not creator_metrics.empty and 'engagement_rate' in creator_metrics.columns and 'conversion_rate' in creator_metrics.columns:
        eng_med = creator_metrics['engagement_rate'].median()
        conv_med = creator_metrics['conversion_rate'].median()
        high_eng_low_conv = creator_metrics[
            (creator_metrics['engagement_rate'] > eng_med) & 
            (creator_metrics['conversion_rate'] < conv_med)
        ]
        if not high_eng_low_conv.empty:
            names = ', '.join(high_eng_low_conv['creator_name'].head(3).tolist()) if 'creator_name' in high_eng_low_conv.columns else f"{len(high_eng_low_conv)} creators"
            avg_eng = high_eng_low_conv['engagement_rate'].mean()
            avg_conv = high_eng_low_conv['conversion_rate'].mean()
            insights.append({
                "id": f"INS-{idx:03d}", "category": "Creator Performance", "severity": "Medium",
                "title": "High Engagement with Relatively Low Conversion Observed",
                "description": (
                    f"{len(high_eng_low_conv)} creator(s) ({names}) show above-median engagement "
                    f"({avg_eng:.1f}% avg) but below-median conversion ({avg_conv:.1f}% avg). "
                    f"Medians: engagement={eng_med:.1f}%, conversion={conv_med:.1f}%. {DISCLAIMER}"
                ),
            })
            idx += 1

    # --- INSIGHT: High Conversion / Low Repeat Purchase ---
    if not creator_metrics.empty and 'conversion_rate' in creator_metrics.columns and 'repeat_purchase_rate' in creator_metrics.columns:
        conv_med = creator_metrics['conversion_rate'].median()
        rep_med = creator_metrics['repeat_purchase_rate'].median()
        high_conv_low_rep = creator_metrics[
            (creator_metrics['conversion_rate'] > conv_med) &
            (creator_metrics['repeat_purchase_rate'] < rep_med)
        ]
        if not high_conv_low_rep.empty:
            avg_conv = high_conv_low_rep['conversion_rate'].mean()
            avg_rep = high_conv_low_rep['repeat_purchase_rate'].mean()
            insights.append({
                "id": f"INS-{idx:03d}", "category": "Retention", "severity": "Medium",
                "title": "High Conversion but Low Repeat Purchase Pattern",
                "description": (
                    f"{len(high_conv_low_rep)} creator(s) drive above-median first-purchase conversion "
                    f"({avg_conv:.1f}% avg) but their customers show below-median repeat rates "
                    f"({avg_rep:.1f}% avg). This may warrant investigation into post-purchase experience. {DISCLAIMER}"
                ),
            })
            idx += 1

    # --- INSIGHT: Funnel Drop-off ---
    if funnel_metrics and len(funnel_metrics) > 1:
        non_first = [s for s in funnel_metrics[1:] if s.get('dropoff_pct', 0) > 0]
        if non_first:
            max_drop = max(non_first, key=lambda x: x.get('dropoff_pct', 0))
            insights.append({
                "id": f"INS-{idx:03d}", "category": "Funnel Efficiency", "severity": "High",
                "title": f"Largest Funnel Drop-off: Before {max_drop['stage']}",
                "description": (
                    f"The biggest funnel drop-off occurs before the '{max_drop['stage']}' stage with "
                    f"{max_drop['dropoff_pct']:.1f}% drop-off (only {max_drop['pct_of_previous']:.1f}% "
                    f"of the previous stage converts). Volume at this stage: {max_drop['volume']:,}. {DISCLAIMER}"
                ),
            })
            idx += 1

    # --- INSIGHT: Content Type Performance ---
    if 'campaigns' in data_dict and not data_dict['campaigns'].empty:
        camps = data_dict['campaigns']
        if 'content_type' in camps.columns:
            from .analytics import build_content_type_metrics
            ct = build_content_type_metrics(data_dict)
            if not ct.empty and 'engagement_rate' in ct.columns and 'conversion_rate' in ct.columns:
                best_eng_ct = ct.loc[ct['engagement_rate'].idxmax()]
                best_conv_ct = ct.loc[ct['conversion_rate'].idxmax()]
                if best_eng_ct['content_type'] != best_conv_ct['content_type']:
                    insights.append({
                        "id": f"INS-{idx:03d}", "category": "Content Strategy", "severity": "Info",
                        "title": "Content Type: Engagement Leader ≠ Conversion Leader",
                        "description": (
                            f"'{best_eng_ct['content_type']}' content leads in engagement rate "
                            f"({best_eng_ct['engagement_rate']:.1f}%) while "
                            f"'{best_conv_ct['content_type']}' leads in conversion rate "
                            f"({best_conv_ct['conversion_rate']:.1f}%). Different content types "
                            f"may serve different stages of the acquisition funnel. {DISCLAIMER}"
                        ),
                    })
                    idx += 1

    # --- INSIGHT: Engagement vs Repeat Purchase Correlation ---
    if not creator_metrics.empty and 'engagement_rate' in creator_metrics.columns and 'repeat_purchase_rate' in creator_metrics.columns:
        corr = creator_metrics['engagement_rate'].corr(creator_metrics['repeat_purchase_rate'])
        if not pd.isna(corr):
            direction = "positive" if corr > 0.1 else ("negative" if corr < -0.1 else "weak/negligible")
            insights.append({
                "id": f"INS-{idx:03d}", "category": "Sustainable Acquisition", "severity": "Info",
                "title": f"Engagement–Repeat Purchase Correlation: {direction.title()}",
                "description": (
                    f"The correlation between engagement rate and repeat purchase rate across creators "
                    f"is {corr:.2f} ({direction}). "
                    + ("Higher engagement is associated with higher repeat purchasing in the observed data. " if corr > 0.1 else
                       "Higher engagement is associated with lower repeat purchasing in the observed data. " if corr < -0.1 else
                       "Engagement rate alone does not appear to strongly predict repeat purchasing. ")
                    + "Correlation indicates association, not causation."
                ),
            })
            idx += 1

    # --- INSIGHT: Top Revenue vs Top Engagement Overlap ---
    if not creator_metrics.empty and 'revenue' in creator_metrics.columns and 'engagement_rate' in creator_metrics.columns:
        n = min(5, len(creator_metrics))
        top_rev = set(creator_metrics.nlargest(n, 'revenue')['creator_id'] if 'creator_id' in creator_metrics.columns else [])
        top_eng = set(creator_metrics.nlargest(n, 'engagement_rate')['creator_id'] if 'creator_id' in creator_metrics.columns else [])
        overlap = top_rev & top_eng
        if top_rev and top_eng:
            insights.append({
                "id": f"INS-{idx:03d}", "category": "Creator Performance", "severity": "Info",
                "title": f"Top Revenue vs Top Engagement Creator Overlap",
                "description": (
                    f"Of the top {n} creators by revenue and top {n} by engagement rate, "
                    f"{len(overlap)} creator(s) appear in both lists. "
                    + (f"Low overlap suggests that high engagement does not automatically translate to highest revenue. " if len(overlap) <= 1 else
                       f"Some overlap exists, but the lists are not identical. ")
                    + DISCLAIMER
                ),
            })
            idx += 1

    # --- INSIGHT: Campaign CAC Variation ---
    if not campaign_metrics.empty and 'cac' in campaign_metrics.columns:
        valid_cac = campaign_metrics[campaign_metrics['cac'] > 0]
        if len(valid_cac) >= 2:
            best = valid_cac.loc[valid_cac['cac'].idxmin()]
            worst = valid_cac.loc[valid_cac['cac'].idxmax()]
            if 'campaign_name' in valid_cac.columns:
                insights.append({
                    "id": f"INS-{idx:03d}", "category": "Campaign Efficiency", "severity": "Medium",
                    "title": "Significant CAC Variation Across Campaigns",
                    "description": (
                        f"Customer acquisition cost ranges from ₹{best['cac']:,.0f} "
                        f"({best['campaign_name']}) to ₹{worst['cac']:,.0f} "
                        f"({worst['campaign_name']}). This {worst['cac']/best['cac']:.1f}x difference "
                        f"may inform budget allocation decisions. {DISCLAIMER}"
                    ),
                })
                idx += 1

    return insights
