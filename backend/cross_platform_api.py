"""
Cross-Platform Analytics API Endpoints

This module provides REST API endpoints for cross-platform analytics including:
- Platform performance comparison and benchmarking
- KPI calculations and cross-platform filtering
- ML-powered platform predictions and recommendations
- Anomaly detection for platform performance
- Statistical modeling for competitive analysis
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from analytics.cross_platform_analytics import CrossPlatformAnalyticsEngine
from auth import get_admin_user

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize cross-platform analytics engine
cross_platform_engine = CrossPlatformAnalyticsEngine()

@router.get("/analytics/cross-platform/overview")
def get_cross_platform_overview(admin_user: dict = Depends(get_admin_user)):
    """
    Get comprehensive overview of all platforms
    
    Returns:
        Cross-platform overview with performance metrics, trends, and insights
    """
    
    try:
        overview = cross_platform_engine.get_platform_overview()
        
        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])
        
        return {
            "overview": overview,
            "metadata": {
                "endpoint": "/analytics/cross-platform/overview",
                "description": "Comprehensive cross-platform performance overview",
                "data_freshness": "real-time",
                "platforms_analyzed": overview.get("total_platforms", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_cross_platform_overview: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/analytics/cross-platform/performance")
def get_platform_performance_comparison(
    include_predictions: bool = Query(default=False, description="Include ML performance predictions"),
    sort_by: str = Query(default="performance_score", description="Sort platforms by metric"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get detailed platform performance comparison with scores and rankings
    
    Args:
        include_predictions: Whether to include ML-based performance predictions
        sort_by: Metric to sort platforms by (performance_score, revenue, customers, etc.)
        
    Returns:
        Platform performance comparison data with rankings and insights
    """
    
    try:
        # Get performance scores
        performances = cross_platform_engine.calculate_platform_performance_scores()
        
        if not performances:
            return {
                "message": "No platform performance data available",
                "platforms": [],
                "total_platforms": 0
            }
        
        # Convert to dict format for JSON response
        performance_data = []
        for perf in performances:
            perf_dict = {
                "platform": perf.platform,
                "total_customers": perf.total_customers,
                "total_orders": perf.total_orders,
                "total_revenue": perf.total_revenue,
                "avg_order_value": perf.avg_order_value,
                "avg_customer_value": perf.avg_customer_value,
                "customer_retention_rate": perf.customer_retention_rate,
                "order_frequency": perf.order_frequency,
                "growth_rate": perf.growth_rate,
                "market_share": perf.market_share,
                "performance_score": perf.performance_score
            }
            performance_data.append(perf_dict)
        
        # Sort by requested metric
        if sort_by in performance_data[0].keys():
            performance_data.sort(key=lambda x: x[sort_by], reverse=True)
        
        response_data = {
            "platforms": performance_data,
            "total_platforms": len(performance_data),
            "top_performer": performance_data[0] if performance_data else None,
            "performance_summary": {
                "total_revenue": sum(p["total_revenue"] for p in performance_data),
                "total_customers": sum(p["total_customers"] for p in performance_data),
                "total_orders": sum(p["total_orders"] for p in performance_data),
                "avg_performance_score": sum(p["performance_score"] for p in performance_data) / len(performance_data) if performance_data else 0
            },
            "sorted_by": sort_by,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # Add predictions if requested
        if include_predictions:
            predictions = cross_platform_engine.predict_platform_performance()
            prediction_data = []
            
            for pred in predictions:
                pred_dict = {
                    "platform": pred.platform,
                    "predicted_revenue_30d": pred.predicted_revenue_30d,
                    "predicted_revenue_90d": pred.predicted_revenue_90d,
                    "predicted_customers_30d": pred.predicted_customers_30d,
                    "predicted_orders_30d": pred.predicted_orders_30d,
                    "confidence_score": pred.confidence_score,
                    "growth_trend": pred.growth_trend,
                    "risk_level": pred.risk_level
                }
                prediction_data.append(pred_dict)
            
            response_data["predictions"] = prediction_data
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error in get_platform_performance_comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/analytics/cross-platform/comparison")
def get_detailed_platform_comparison(
    metrics: Optional[str] = Query(default=None, description="Comma-separated list of metrics to compare"),
    platforms: Optional[str] = Query(default=None, description="Comma-separated list of platforms to include"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get detailed comparison analysis between platforms
    
    Args:
        metrics: Specific metrics to compare (revenue, customers, orders, aov, clv, retention)
        platforms: Specific platforms to include in comparison
        
    Returns:
        Detailed platform comparison with insights and recommendations
    """
    
    try:
        # Parse parameters
        metrics_list = metrics.split(',') if metrics else None
        platforms_list = platforms.split(',') if platforms else None
        
        # Get comparison data
        comparison = cross_platform_engine.generate_platform_comparison(metrics_list)
        
        if "error" in comparison:
            raise HTTPException(status_code=500, detail=comparison["error"])
        
        # Filter platforms if specified
        if platforms_list:
            comparison["comparison_matrix"] = [
                p for p in comparison["comparison_matrix"] 
                if p["platform"] in platforms_list
            ]
            comparison["performance_rankings"] = [
                r for r in comparison["performance_rankings"] 
                if r["platform"] in platforms_list
            ]
        
        return {
            "comparison": comparison,
            "filters_applied": {
                "metrics": metrics_list,
                "platforms": platforms_list
            },
            "metadata": {
                "endpoint": "/analytics/cross-platform/comparison",
                "description": "Detailed cross-platform comparison analysis",
                "platforms_compared": len(comparison.get("comparison_matrix", [])),
                "metrics_analyzed": len(metrics_list) if metrics_list else "all"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_detailed_platform_comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/analytics/cross-platform/predictions")
def get_platform_predictions(
    days_ahead: int = Query(default=30, description="Number of days to predict ahead"),
    platform: Optional[str] = Query(default=None, description="Specific platform to predict for"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get ML-powered platform performance predictions
    
    Args:
        days_ahead: Number of days to predict ahead (default: 30)
        platform: Specific platform to get predictions for
        
    Returns:
        Platform performance predictions with confidence scores and trends
    """
    
    try:
        predictions = cross_platform_engine.predict_platform_performance(days_ahead)
        
        if not predictions:
            return {
                "message": "No prediction data available",
                "predictions": [],
                "total_platforms": 0
            }
        
        # Convert to dict format
        prediction_data = []
        for pred in predictions:
            pred_dict = {
                "platform": pred.platform,
                "predicted_revenue_30d": pred.predicted_revenue_30d,
                "predicted_revenue_90d": pred.predicted_revenue_90d,
                "predicted_customers_30d": pred.predicted_customers_30d,
                "predicted_orders_30d": pred.predicted_orders_30d,
                "confidence_score": pred.confidence_score,
                "growth_trend": pred.growth_trend,
                "risk_level": pred.risk_level
            }
            prediction_data.append(pred_dict)
        
        # Filter by platform if specified
        if platform:
            prediction_data = [p for p in prediction_data if p["platform"] == platform]
        
        # Calculate summary statistics
        total_predicted_revenue = sum(p["predicted_revenue_30d"] for p in prediction_data)
        total_predicted_customers = sum(p["predicted_customers_30d"] for p in prediction_data)
        avg_confidence = sum(p["confidence_score"] for p in prediction_data) / len(prediction_data) if prediction_data else 0
        
        return {
            "predictions": prediction_data,
            "prediction_summary": {
                "total_predicted_revenue_30d": total_predicted_revenue,
                "total_predicted_customers_30d": total_predicted_customers,
                "average_confidence_score": avg_confidence,
                "high_growth_platforms": len([p for p in prediction_data if p["growth_trend"] == "growing"]),
                "high_risk_platforms": len([p for p in prediction_data if p["risk_level"] == "high"])
            },
            "prediction_parameters": {
                "days_ahead": days_ahead,
                "platform_filter": platform,
                "total_platforms_analyzed": len(prediction_data)
            },
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in get_platform_predictions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/analytics/cross-platform/anomalies")
def get_platform_anomalies(admin_user: dict = Depends(get_admin_user)):
    """
    Detect and return platform performance anomalies
    
    Returns:
        Platform anomalies with severity levels and recommendations
    """
    
    try:
        anomalies = cross_platform_engine.detect_platform_anomalies()
        
        if "error" in anomalies:
            raise HTTPException(status_code=500, detail=anomalies["error"])
        
        return {
            "anomaly_detection": anomalies,
            "metadata": {
                "endpoint": "/analytics/cross-platform/anomalies",
                "description": "Platform performance anomaly detection",
                "detection_method": "statistical_analysis",
                "analysis_period": "last_30_days"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_platform_anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/analytics/cross-platform/recommendations")
def get_platform_recommendations(admin_user: dict = Depends(get_admin_user)):
    """
    Get actionable recommendations for platform optimization
    
    Returns:
        Platform-specific and global recommendations for performance improvement
    """
    
    try:
        recommendations = cross_platform_engine.generate_platform_recommendations()
        
        if "error" in recommendations:
            raise HTTPException(status_code=500, detail=recommendations["error"])
        
        return {
            "recommendations": recommendations,
            "metadata": {
                "endpoint": "/analytics/cross-platform/recommendations",
                "description": "AI-powered platform optimization recommendations",
                "recommendation_types": ["revenue_optimization", "retention_improvement", "market_expansion", "strategic"],
                "analysis_basis": "performance_scores_and_predictions"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_platform_recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/analytics/cross-platform/kpis")
def get_cross_platform_kpis(
    platform: Optional[str] = Query(default=None, description="Filter by specific platform"),
    date_range: Optional[str] = Query(default="30d", description="Date range for KPI calculation"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get key performance indicators across platforms
    
    Args:
        platform: Specific platform to get KPIs for
        date_range: Date range for calculations (30d, 90d, 1y)
        
    Returns:
        Cross-platform KPIs with comparisons and trends
    """
    
    try:
        # Get platform overview data which includes KPIs
        overview = cross_platform_engine.get_platform_overview()
        
        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])
        
        # Extract and format KPIs
        platform_data = overview.get("platform_overview", [])
        order_data = overview.get("order_analytics", [])
        
        # Combine data for comprehensive KPIs
        kpis = []
        for platform_info in platform_data:
            platform_name = platform_info["platform"]
            
            # Find corresponding order data
            order_info = next((o for o in order_data if o["platform"] == platform_name), {})
            
            # Calculate additional KPIs
            total_customers = platform_info.get("total_customers", 0)
            active_customers = platform_info.get("active_customers", 0)
            
            activation_rate = (active_customers / total_customers * 100) if total_customers > 0 else 0
            
            platform_kpis = {
                "platform": platform_name,
                "revenue_kpis": {
                    "total_revenue": platform_info.get("total_revenue", 0),
                    "avg_customer_value": platform_info.get("avg_customer_value", 0),
                    "avg_order_value": order_info.get("avg_order_value", 0)
                },
                "customer_kpis": {
                    "total_customers": total_customers,
                    "active_customers": active_customers,
                    "customer_activation_rate": activation_rate,
                    "avg_orders_per_customer": platform_info.get("avg_orders_per_customer", 0)
                },
                "operational_kpis": {
                    "total_orders": order_info.get("total_orders", 0),
                    "completed_orders": order_info.get("completed_orders", 0),
                    "order_completion_rate": (order_info.get("completed_orders", 0) / order_info.get("total_orders", 1) * 100) if order_info.get("total_orders", 0) > 0 else 0,
                    "avg_recency_days": order_info.get("avg_recency_days", 0)
                }
            }
            
            kpis.append(platform_kpis)
        
        # Filter by platform if specified
        if platform:
            kpis = [k for k in kpis if k["platform"] == platform]
        
        # Calculate cross-platform summary KPIs
        summary_kpis = {
            "total_revenue": sum(k["revenue_kpis"]["total_revenue"] for k in kpis),
            "total_customers": sum(k["customer_kpis"]["total_customers"] for k in kpis),
            "total_orders": sum(k["operational_kpis"]["total_orders"] for k in kpis),
            "avg_cross_platform_clv": sum(k["revenue_kpis"]["avg_customer_value"] for k in kpis) / len(kpis) if kpis else 0,
            "avg_cross_platform_aov": sum(k["revenue_kpis"]["avg_order_value"] for k in kpis) / len(kpis) if kpis else 0,
            "platforms_analyzed": len(kpis)
        }
        
        return {
            "platform_kpis": kpis,
            "cross_platform_summary": summary_kpis,
            "parameters": {
                "platform_filter": platform,
                "date_range": date_range,
                "platforms_included": [k["platform"] for k in kpis]
            },
            "metadata": {
                "endpoint": "/analytics/cross-platform/kpis",
                "description": "Cross-platform Key Performance Indicators",
                "kpi_categories": ["revenue_kpis", "customer_kpis", "operational_kpis"],
                "calculation_basis": "universal_schema_data"
            },
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in get_cross_platform_kpis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/analytics/cross-platform/health")
def get_platform_health_check(admin_user: dict = Depends(get_admin_user)):
    """
    Get health status of cross-platform analytics system
    
    Returns:
        System health status and data availability
    """
    
    try:
        # Test basic connectivity and data availability
        overview = cross_platform_engine.get_platform_overview()
        
        if "error" in overview:
            return {
                "status": "unhealthy",
                "error": overview["error"],
                "timestamp": datetime.now().isoformat()
            }
        
        platform_count = overview.get("total_platforms", 0)
        total_customers = sum(p.get("total_customers", 0) for p in overview.get("platform_overview", []))
        
        health_status = {
            "status": "healthy",
            "system_info": {
                "platforms_connected": platform_count,
                "total_customers_available": total_customers,
                "data_freshness": "real-time",
                "last_updated": overview.get("analysis_timestamp")
            },
            "capabilities": {
                "performance_analysis": True,
                "ml_predictions": True,
                "anomaly_detection": True,
                "recommendations": True,
                "cross_platform_comparison": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in get_platform_health_check: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }