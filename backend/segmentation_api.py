"""
Customer Segmentation API Endpoints

This module provides REST API endpoints for customer segmentation analytics including:
- RFM analysis and scoring
- ML-powered customer clustering
- Segment-based business insights
- Customer profile analytics
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from analytics.customer_segmentation import CustomerSegmentationEngine, CustomerSegmentProfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize segmentation engine
segmentation_engine = CustomerSegmentationEngine()

@router.get("/analytics/segmentation/rfm")
def get_rfm_analysis(
    platform: Optional[str] = None,
    include_details: bool = Query(default=False, description="Include detailed RFM breakdown")
):
    """
    Get RFM (Recency, Frequency, Monetary) analysis for customers
    
    Args:
        platform: Filter by platform (optional)
        include_details: Whether to include detailed customer-level data
        
    Returns:
        RFM analysis with scores and segment assignments
    """
    
    try:
        # Calculate RFM scores
        rfm_df = segmentation_engine.calculate_rfm_scores(platform)
        
        if rfm_df.empty:
            return {
                "message": "No customers found for RFM analysis",
                "total_customers": 0,
                "rfm_data": []
            }
        
        # Summary statistics
        summary = {
            "total_customers": len(rfm_df),
            "platform_filter": platform,
            "avg_recency_days": float(rfm_df['recency_days'].mean()),
            "avg_frequency": float(rfm_df['frequency_count'].mean()),
            "avg_monetary_value": float(rfm_df['monetary_value'].mean()),
            "segment_distribution": rfm_df['rfm_segment'].value_counts().to_dict()
        }
        
        # Detailed customer data (if requested)
        customers_data = []
        if include_details:
            for _, customer in rfm_df.iterrows():
                customers_data.append({
                    "customer_id": customer['customer_id'],
                    "platform": customer['platform'],
                    "email": customer['email'],
                    "name": f"{customer['first_name']} {customer['last_name']}".strip(),
                    "rfm_scores": {
                        "recency": int(customer['recency_score']),
                        "frequency": int(customer['frequency_score']),
                        "monetary": int(customer['monetary_score']),
                        "combined": customer['rfm_score']
                    },
                    "rfm_values": {
                        "recency_days": int(customer['recency_days']),
                        "frequency_count": int(customer['frequency_count']),
                        "monetary_value": float(customer['monetary_value']),
                        "avg_order_value": float(customer['avg_order_value'])
                    },
                    "segment": customer['rfm_segment'],
                    "churn_risk_score": float(customer['churn_risk_score']),
                    "customer_lifespan_days": int(customer['customer_lifespan_days'])
                })
        
        return {
            "summary": summary,
            "rfm_data": customers_data,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"RFM analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RFM analysis error: {str(e)}")


@router.get("/analytics/segmentation/profiles")
def get_customer_segment_profiles(
    platform: Optional[str] = None,
    segment: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    sort_by: str = Query(default="monetary", regex="^(monetary|frequency|recency|risk)$")
):
    """
    Get comprehensive customer segment profiles
    
    Args:
        platform: Filter by platform
        segment: Filter by specific segment
        limit: Maximum number of profiles to return
        sort_by: Sort criteria (monetary, frequency, recency, risk)
        
    Returns:
        List of detailed customer segment profiles
    """
    
    try:
        # Create customer profiles
        profiles = segmentation_engine.create_customer_profiles(platform)
        
        if not profiles:
            return {
                "profiles": [],
                "summary": {
                    "total_profiles": 0,
                    "message": "No customer profiles found"
                }
            }
        
        # Filter by segment if specified
        if segment:
            profiles = [p for p in profiles if p.business_segment == segment]
        
        # Sort profiles
        if sort_by == "monetary":
            profiles.sort(key=lambda x: x.monetary_value, reverse=True)
        elif sort_by == "frequency":
            profiles.sort(key=lambda x: x.frequency_count, reverse=True)
        elif sort_by == "recency":
            profiles.sort(key=lambda x: x.recency_days)
        elif sort_by == "risk":
            profiles.sort(key=lambda x: x.churn_risk_score, reverse=True)
        
        # Limit results
        profiles = profiles[:limit]
        
        # Format response
        formatted_profiles = []
        for profile in profiles:
            formatted_profiles.append({
                "customer_id": profile.customer_id,
                "platform": profile.platform,
                "rfm_analysis": {
                    "recency_score": profile.recency_score,
                    "frequency_score": profile.frequency_score,
                    "monetary_score": profile.monetary_score,
                    "rfm_score": profile.rfm_score,
                    "recency_days": profile.recency_days,
                    "frequency_count": profile.frequency_count,
                    "monetary_value": profile.monetary_value
                },
                "segmentation": {
                    "rfm_segment": profile.rfm_segment,
                    "ml_segment": profile.ml_segment,
                    "business_segment": profile.business_segment,
                    "segment_priority": profile.segment_priority,
                    "segment_confidence": profile.segment_confidence
                },
                "metrics": {
                    "avg_order_value": profile.avg_order_value,
                    "customer_lifespan_days": profile.customer_lifespan_days,
                    "churn_risk_score": profile.churn_risk_score
                },
                "recommendations": {
                    "actions": profile.recommended_actions,
                    "priority_level": profile.segment_priority
                }
            })
        
        return {
            "profiles": formatted_profiles,
            "summary": {
                "total_profiles": len(formatted_profiles),
                "platform_filter": platform,
                "segment_filter": segment,
                "sort_criteria": sort_by
            },
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Customer profiles retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Profiles error: {str(e)}")


@router.get("/analytics/segmentation/summary")
def get_segmentation_summary(platform: Optional[str] = None):
    """
    Get comprehensive segmentation summary with business insights
    
    Args:
        platform: Filter by platform (optional)
        
    Returns:
        Segmentation summary with key metrics and insights
    """
    
    try:
        # Create customer profiles
        profiles = segmentation_engine.create_customer_profiles(platform)
        
        if not profiles:
            return {
                "error": "No customer data available for segmentation analysis",
                "total_customers": 0
            }
        
        # Get summary statistics
        summary = segmentation_engine.get_segment_summary(profiles)
        
        # Add additional business metrics
        total_revenue = sum(p.monetary_value for p in profiles)
        avg_customer_value = total_revenue / len(profiles) if profiles else 0
        
        # High-value customer analysis
        vip_customers = [p for p in profiles if p.business_segment in ['Champions', 'Cannot Lose Them']]
        vip_revenue = sum(p.monetary_value for p in vip_customers)
        vip_percentage = (len(vip_customers) / len(profiles)) * 100 if profiles else 0
        
        # Risk analysis
        high_risk_customers = [p for p in profiles if p.churn_risk_score > 0.7]
        at_risk_revenue = sum(p.monetary_value for p in high_risk_customers)
        
        # Segment performance rankings
        segment_performance = {}
        for segment in set(p.business_segment for p in profiles):
            segment_customers = [p for p in profiles if p.business_segment == segment]
            segment_performance[segment] = {
                "customer_count": len(segment_customers),
                "total_revenue": sum(p.monetary_value for p in segment_customers),
                "avg_customer_value": sum(p.monetary_value for p in segment_customers) / len(segment_customers),
                "avg_churn_risk": sum(p.churn_risk_score for p in segment_customers) / len(segment_customers)
            }
        
        enhanced_summary = {
            **summary,
            "business_metrics": {
                "total_revenue": total_revenue,
                "avg_customer_value": avg_customer_value,
                "vip_analysis": {
                    "vip_customer_count": len(vip_customers),
                    "vip_revenue": vip_revenue,
                    "vip_percentage": vip_percentage,
                    "vip_revenue_share": (vip_revenue / total_revenue * 100) if total_revenue > 0 else 0
                },
                "risk_analysis": {
                    "high_risk_count": len(high_risk_customers),
                    "at_risk_revenue": at_risk_revenue,
                    "risk_percentage": (len(high_risk_customers) / len(profiles)) * 100,
                    "revenue_at_risk": (at_risk_revenue / total_revenue * 100) if total_revenue > 0 else 0
                }
            },
            "segment_performance": segment_performance,
            "platform_filter": platform,
            "calculated_at": datetime.now().isoformat()
        }
        
        return enhanced_summary
        
    except Exception as e:
        logger.error(f"Segmentation summary failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summary error: {str(e)}")


@router.get("/analytics/segmentation/segments/{segment_name}")
def get_segment_details(
    segment_name: str,
    platform: Optional[str] = None,
    include_customers: bool = Query(default=True, description="Include customer list")
):
    """
    Get detailed analysis for a specific customer segment
    
    Args:
        segment_name: Name of the segment to analyze
        platform: Filter by platform (optional)
        include_customers: Whether to include customer details
        
    Returns:
        Detailed segment analysis with customer data
    """
    
    try:
        # Create customer profiles
        profiles = segmentation_engine.create_customer_profiles(platform)
        
        # Filter by segment
        segment_profiles = [p for p in profiles if p.business_segment == segment_name]
        
        if not segment_profiles:
            raise HTTPException(
                status_code=404, 
                detail=f"Segment '{segment_name}' not found or has no customers"
            )
        
        # Segment metrics
        total_customers = len(segment_profiles)
        total_revenue = sum(p.monetary_value for p in segment_profiles)
        avg_customer_value = total_revenue / total_customers
        avg_order_frequency = sum(p.frequency_count for p in segment_profiles) / total_customers
        avg_recency = sum(p.recency_days for p in segment_profiles) / total_customers
        avg_churn_risk = sum(p.churn_risk_score for p in segment_profiles) / total_customers
        
        # Get segment definition
        segment_info = segmentation_engine.rfm_segments.get(segment_name, {})
        
        # Customer details (if requested)
        customers = []
        if include_customers:
            for profile in segment_profiles[:50]:  # Limit to first 50 customers
                customers.append({
                    "customer_id": profile.customer_id,
                    "platform": profile.platform,
                    "monetary_value": profile.monetary_value,
                    "frequency_count": profile.frequency_count,
                    "recency_days": profile.recency_days,
                    "churn_risk_score": profile.churn_risk_score,
                    "rfm_score": profile.rfm_score
                })
        
        return {
            "segment_name": segment_name,
            "segment_definition": {
                "description": segment_info.get('description', 'No description available'),
                "priority": segment_info.get('priority', 1),
                "recommended_actions": segment_info.get('actions', [])
            },
            "segment_metrics": {
                "total_customers": total_customers,
                "total_revenue": total_revenue,
                "avg_customer_value": avg_customer_value,
                "avg_order_frequency": avg_order_frequency,
                "avg_recency_days": avg_recency,
                "avg_churn_risk": avg_churn_risk,
                "revenue_percentage": (total_revenue / sum(p.monetary_value for p in profiles) * 100) if profiles else 0
            },
            "customers": customers,
            "platform_filter": platform,
            "calculated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Segment details retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Segment analysis error: {str(e)}")


@router.get("/analytics/segmentation/ml-clusters")
def get_ml_clustering_analysis(
    platform: Optional[str] = None,
    n_clusters: int = Query(default=5, ge=2, le=10)
):
    """
    Get ML-powered customer clustering analysis
    
    Args:
        platform: Filter by platform (optional)
        n_clusters: Number of clusters for K-means (2-10)
        
    Returns:
        ML clustering results with cluster characteristics
    """
    
    try:
        # Get RFM data
        rfm_df = segmentation_engine.calculate_rfm_scores(platform)
        
        if rfm_df.empty:
            return {
                "message": "No customer data available for ML clustering",
                "clusters": []
            }
        
        # Perform clustering
        clustered_df = segmentation_engine.perform_kmeans_clustering(rfm_df, n_clusters)
        
        # Analyze clusters
        cluster_analysis = {}
        for cluster in clustered_df['ml_cluster'].unique():
            cluster_data = clustered_df[clustered_df['ml_cluster'] == cluster]
            
            cluster_analysis[int(cluster)] = {
                "cluster_name": cluster_data['ml_segment'].iloc[0],
                "customer_count": len(cluster_data),
                "characteristics": {
                    "avg_recency_days": float(cluster_data['recency_days'].mean()),
                    "avg_frequency": float(cluster_data['frequency_count'].mean()),
                    "avg_monetary_value": float(cluster_data['monetary_value'].mean()),
                    "avg_churn_risk": float(cluster_data['churn_risk_score'].mean())
                },
                "top_customers": [
                    {
                        "customer_id": row['customer_id'],
                        "platform": row['platform'],
                        "monetary_value": float(row['monetary_value'])
                    }
                    for _, row in cluster_data.nlargest(3, 'monetary_value').iterrows()
                ]
            }
        
        return {
            "ml_clustering_results": {
                "total_customers": len(clustered_df),
                "number_of_clusters": n_clusters,
                "platform_filter": platform,
                "clusters": cluster_analysis
            },
            "clustering_quality": {
                "note": "Silhouette score and other metrics available in logs"
            },
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"ML clustering analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ML clustering error: {str(e)}")


@router.get("/analytics/segmentation/recommendations/{customer_id}")
def get_customer_recommendations(
    customer_id: str,
    platform: Optional[str] = None
):
    """
    Get personalized recommendations for a specific customer
    
    Args:
        customer_id: External customer ID
        platform: Platform identifier (optional)
        
    Returns:
        Personalized customer recommendations based on segment
    """
    
    try:
        # Get customer profiles
        profiles = segmentation_engine.create_customer_profiles(platform)
        
        # Find specific customer
        customer_profile = None
        for profile in profiles:
            if profile.customer_id == customer_id:
                customer_profile = profile
                break
        
        if not customer_profile:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {customer_id} not found"
            )
        
        # Get segment information
        segment_info = segmentation_engine.rfm_segments.get(customer_profile.business_segment, {})
        
        # Generate personalized recommendations
        recommendations = {
            "customer_id": customer_id,
            "customer_analysis": {
                "segment": customer_profile.business_segment,
                "segment_priority": customer_profile.segment_priority,
                "churn_risk": customer_profile.churn_risk_score,
                "risk_level": "High" if customer_profile.churn_risk_score > 0.7 else "Medium" if customer_profile.churn_risk_score > 0.4 else "Low",
                "lifetime_value": customer_profile.monetary_value
            },
            "segment_recommendations": {
                "description": segment_info.get('description', 'No description available'),
                "recommended_actions": customer_profile.recommended_actions,
                "urgency": "High" if customer_profile.segment_priority >= 4 else "Medium" if customer_profile.segment_priority >= 2 else "Low"
            },
            "personalized_insights": _generate_personalized_insights(customer_profile),
            "calculated_at": datetime.now().isoformat()
        }
        
        return recommendations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer recommendations failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Recommendations error: {str(e)}")


def _generate_personalized_insights(profile: CustomerSegmentProfile) -> List[str]:
    """
    Generate personalized insights for a customer
    
    Args:
        profile: Customer segment profile
        
    Returns:
        List of personalized insights
    """
    
    insights = []
    
    # Recency insights
    if profile.recency_days > 90:
        insights.append(f"Customer hasn't purchased in {profile.recency_days} days - immediate re-engagement needed")
    elif profile.recency_days > 30:
        insights.append(f"Customer last purchased {profile.recency_days} days ago - consider follow-up")
    else:
        insights.append(f"Customer is active with recent purchase {profile.recency_days} days ago")
    
    # Frequency insights
    if profile.frequency_count == 1:
        insights.append("One-time buyer - focus on second purchase conversion")
    elif profile.frequency_count >= 5:
        insights.append(f"Loyal customer with {profile.frequency_count} orders - reward loyalty")
    
    # Monetary insights
    if profile.monetary_value > 1000:
        insights.append(f"High-value customer (${profile.monetary_value:.2f} total) - VIP treatment recommended")
    elif profile.avg_order_value > 200:
        insights.append(f"High AOV customer (${profile.avg_order_value:.2f}) - upsell opportunities")
    
    # Churn risk insights
    if profile.churn_risk_score > 0.8:
        insights.append("Critical churn risk - immediate intervention required")
    elif profile.churn_risk_score > 0.5:
        insights.append("Moderate churn risk - proactive retention recommended")
    
    return insights[:4]  # Return top 4 insights