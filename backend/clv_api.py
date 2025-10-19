"""
CLV Analytics API Endpoints

This module provides REST API endpoints for Customer Lifetime Value calculations
and related analytics, integrating with the existing Nexus Analytics system.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from analytics.clv_calculator import CLVCalculator, CLVMetrics
from advanced_clv import get_advanced_clv_insights, AdvancedCLVPredictor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize CLV calculator
clv_calculator = CLVCalculator()

@router.get("/analytics/clv/customer/{customer_external_id}")
def get_customer_clv(
    customer_external_id: str,
    platform: Optional[str] = None
):
    """
    Get comprehensive CLV analysis for a specific customer
    
    Args:
        customer_external_id: External customer ID from platform
        platform: Platform identifier (optional)
        
    Returns:
        Detailed CLV metrics including traditional CLV, confidence intervals, risk score
    """
    
    try:
        clv_metrics = clv_calculator.calculate_basic_clv(customer_external_id, platform)
        
        return {
            "customer_id": clv_metrics.customer_id,
            "platform": clv_metrics.platform,
            "clv_analysis": {
                "traditional_clv": clv_metrics.traditional_clv,
                "confidence_interval": {
                    "low": clv_metrics.confidence_interval_low,
                    "high": clv_metrics.confidence_interval_high
                },
                "risk_assessment": {
                    "churn_risk_score": clv_metrics.risk_score,
                    "risk_level": _get_risk_level(clv_metrics.risk_score),
                    "days_since_last_order": clv_metrics.days_since_last_order
                },
                "segment": clv_metrics.segment
            },
            "metrics": {
                "avg_order_value": clv_metrics.avg_order_value,
                "purchase_frequency": clv_metrics.purchase_frequency,
                "customer_lifespan_days": clv_metrics.customer_lifespan_days,
                "total_orders": clv_metrics.total_orders,
                "total_spent": clv_metrics.total_spent
            },
            "last_order_date": clv_metrics.last_order_date.isoformat() if clv_metrics.last_order_date else None,
            "calculated_at": datetime.now().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"CLV calculation failed for customer {customer_external_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CLV calculation error: {str(e)}")


@router.get("/analytics/clv/bulk")
def get_bulk_clv_analysis(
    platform: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    sort_by: str = Query(default="clv", regex="^(clv|risk|frequency|value)$"),
    order: str = Query(default="desc", regex="^(asc|desc)$")
):
    """
    Get CLV analysis for multiple customers
    
    Args:
        platform: Filter by platform
        limit: Maximum number of customers to analyze
        sort_by: Sort criteria (clv, risk, frequency, value)
        order: Sort order (asc, desc)
        
    Returns:
        List of customer CLV analyses with summary statistics
    """
    
    try:
        clv_results = clv_calculator.calculate_bulk_clv(platform, limit)
        
        if not clv_results:
            return {
                "customers": [],
                "summary": {
                    "total_customers": 0,
                    "avg_clv": 0,
                    "total_estimated_value": 0
                }
            }
        
        # Sort results
        if sort_by == "clv":
            clv_results.sort(key=lambda x: x.traditional_clv, reverse=(order == "desc"))
        elif sort_by == "risk":
            clv_results.sort(key=lambda x: x.risk_score, reverse=(order == "desc"))
        elif sort_by == "frequency":
            clv_results.sort(key=lambda x: x.purchase_frequency, reverse=(order == "desc"))
        elif sort_by == "value":
            clv_results.sort(key=lambda x: x.total_spent, reverse=(order == "desc"))
        
        # Format response
        customers = []
        for metrics in clv_results:
            customers.append({
                "customer_id": metrics.customer_id,
                "platform": metrics.platform,
                "clv": metrics.traditional_clv,
                "confidence_range": {
                    "low": metrics.confidence_interval_low,
                    "high": metrics.confidence_interval_high
                },
                "risk_score": metrics.risk_score,
                "risk_level": _get_risk_level(metrics.risk_score),
                "segment": metrics.segment,
                "metrics": {
                    "avg_order_value": metrics.avg_order_value,
                    "purchase_frequency": metrics.purchase_frequency,
                    "total_orders": metrics.total_orders,
                    "total_spent": metrics.total_spent,
                    "days_since_last_order": metrics.days_since_last_order
                }
            })
        
        # Calculate summary statistics
        total_clv = sum(m.traditional_clv for m in clv_results)
        avg_clv = total_clv / len(clv_results) if clv_results else 0
        
        # Segment distribution
        segment_counts = {}
        risk_distribution = {"low": 0, "medium": 0, "high": 0}
        
        for metrics in clv_results:
            segment_counts[metrics.segment] = segment_counts.get(metrics.segment, 0) + 1
            risk_level = _get_risk_level(metrics.risk_score)
            risk_distribution[risk_level] += 1
        
        return {
            "customers": customers,
            "summary": {
                "total_customers": len(clv_results),
                "avg_clv": avg_clv,
                "total_estimated_value": total_clv,
                "platform_filter": platform,
                "segment_distribution": segment_counts,
                "risk_distribution": risk_distribution
            },
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Bulk CLV calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk CLV calculation error: {str(e)}")


@router.get("/analytics/clv/platform-summary")
def get_platform_clv_summary(platform: Optional[str] = None):
    """
    Get CLV summary statistics by platform
    
    Args:
        platform: Specific platform to analyze (optional)
        
    Returns:
        Platform-wise CLV summaries with key metrics
    """
    
    try:
        summary = clv_calculator.get_platform_clv_summary(platform)
        
        # Enhance with CLV insights
        for platform_data in summary["platform_summaries"]:
            # Calculate CLV health indicators
            platform_data["clv_health"] = _assess_platform_clv_health(platform_data)
            
            # Add recommendations
            platform_data["recommendations"] = _generate_platform_recommendations(platform_data)
        
        return summary
        
    except Exception as e:
        logger.error(f"Platform CLV summary failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Platform summary error: {str(e)}")


@router.get("/analytics/clv/segments")
def get_clv_segments_analysis(
    platform: Optional[str] = None,
    include_predictions: bool = False
):
    """
    Get detailed CLV analysis by customer segments
    
    Args:
        platform: Filter by platform
        include_predictions: Include ML predictions (if available)
        
    Returns:
        Segment-wise CLV analysis with actionable insights
    """
    
    try:
        # Get bulk CLV data for segmentation
        clv_results = clv_calculator.calculate_bulk_clv(platform, limit=1000)
        
        if not clv_results:
            return {"segments": [], "analysis_date": datetime.now().isoformat()}
        
        # Group by segments
        segments = {}
        for metrics in clv_results:
            segment = metrics.segment
            if segment not in segments:
                segments[segment] = {
                    "segment": segment,
                    "customers": [],
                    "metrics": {
                        "count": 0,
                        "avg_clv": 0,
                        "total_clv": 0,
                        "avg_risk_score": 0,
                        "avg_order_value": 0,
                        "avg_frequency": 0,
                        "avg_total_spent": 0
                    }
                }
            
            segments[segment]["customers"].append(metrics)
        
        # Calculate segment statistics
        segment_analysis = []
        for segment_name, segment_data in segments.items():
            customers = segment_data["customers"]
            count = len(customers)
            
            segment_summary = {
                "segment": segment_name,
                "customer_count": count,
                "percentage_of_total": (count / len(clv_results)) * 100,
                "avg_clv": sum(c.traditional_clv for c in customers) / count,
                "total_clv": sum(c.traditional_clv for c in customers),
                "avg_risk_score": sum(c.risk_score for c in customers) / count,
                "avg_order_value": sum(c.avg_order_value for c in customers) / count,
                "avg_purchase_frequency": sum(c.purchase_frequency for c in customers) / count,
                "avg_total_spent": sum(c.total_spent for c in customers) / count,
                "retention_insights": _analyze_segment_retention(customers),
                "recommendations": _generate_segment_recommendations(segment_name, customers)
            }
            
            segment_analysis.append(segment_summary)
        
        # Sort by total CLV contribution
        segment_analysis.sort(key=lambda x: x["total_clv"], reverse=True)
        
        return {
            "segments": segment_analysis,
            "total_customers_analyzed": len(clv_results),
            "platform_filter": platform,
            "analysis_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"CLV segments analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Segments analysis error: {str(e)}")


@router.get("/analytics/clv/trends")
def get_clv_trends(
    platform: Optional[str] = None,
    days_back: int = Query(default=90, le=365)
):
    """
    Get CLV trends and patterns over time
    
    Args:
        platform: Filter by platform
        days_back: Number of days to analyze
        
    Returns:
        CLV trends with time-based insights
    """
    
    try:
        # This is a placeholder for trend analysis
        # In a full implementation, you would track CLV changes over time
        
        summary = clv_calculator.get_platform_clv_summary(platform)
        
        # Generate trend insights based on current data
        trends = []
        for platform_data in summary["platform_summaries"]:
            trend_data = {
                "platform": platform_data["platform"],
                "current_avg_clv": platform_data["estimated_avg_clv"],
                "customer_growth_rate": _estimate_growth_rate(platform_data),
                "churn_trend": _estimate_churn_trend(platform_data),
                "clv_health_trend": "stable",  # Placeholder
                "recommended_actions": _generate_trend_recommendations(platform_data)
            }
            trends.append(trend_data)
        
        return {
            "trends": trends,
            "analysis_period_days": days_back,
            "analysis_date": datetime.now().isoformat(),
            "note": "Trend analysis enhanced with historical tracking in future versions"
        }
        
    except Exception as e:
        logger.error(f"CLV trends analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trends analysis error: {str(e)}")


# Helper functions
def _get_risk_level(risk_score: float) -> str:
    """Convert risk score to human-readable level"""
    if risk_score >= 0.7:
        return "high"
    elif risk_score >= 0.4:
        return "medium"
    else:
        return "low"


def _assess_platform_clv_health(platform_data: Dict) -> str:
    """Assess overall CLV health for a platform"""
    retention_rate = platform_data.get("retention_rate", 0)
    avg_clv = platform_data.get("estimated_avg_clv", 0)
    
    if retention_rate >= 70 and avg_clv >= 1000:
        return "excellent"
    elif retention_rate >= 50 and avg_clv >= 500:
        return "good"
    elif retention_rate >= 30 and avg_clv >= 200:
        return "fair"
    else:
        return "needs_improvement"


def _generate_platform_recommendations(platform_data: Dict) -> List[str]:
    """Generate actionable recommendations for platform CLV improvement"""
    recommendations = []
    
    retention_rate = platform_data.get("retention_rate", 0)
    at_risk_customers = platform_data.get("at_risk_customers", 0)
    one_time_customers = platform_data.get("one_time_customers", 0)
    
    if retention_rate < 50:
        recommendations.append("Focus on customer retention programs and loyalty initiatives")
    
    if at_risk_customers > 0:
        recommendations.append(f"Re-engage {at_risk_customers} at-risk customers with targeted campaigns")
    
    if one_time_customers > 0:
        recommendations.append(f"Convert {one_time_customers} one-time buyers with follow-up offers")
    
    if platform_data.get("avg_order_value", 0) < 100:
        recommendations.append("Implement upselling strategies to increase average order value")
    
    return recommendations


def _analyze_segment_retention(customers: List[CLVMetrics]) -> Dict:
    """Analyze retention characteristics for a customer segment"""
    total_customers = len(customers)
    at_risk_count = sum(1 for c in customers if c.risk_score >= 0.7)
    avg_days_since_order = sum(c.days_since_last_order for c in customers) / total_customers
    
    return {
        "at_risk_percentage": (at_risk_count / total_customers) * 100,
        "avg_days_since_last_order": avg_days_since_order,
        "retention_health": "good" if at_risk_count / total_customers < 0.3 else "concerning"
    }


def _generate_segment_recommendations(segment_name: str, customers: List[CLVMetrics]) -> List[str]:
    """Generate recommendations for specific customer segments"""
    recommendations = []
    
    avg_risk = sum(c.risk_score for c in customers) / len(customers)
    avg_frequency = sum(c.purchase_frequency for c in customers) / len(customers)
    
    if segment_name == "VIP":
        recommendations.extend([
            "Provide exclusive perks and early access to new products",
            "Assign dedicated customer success managers",
            "Create VIP loyalty program with premium benefits"
        ])
    elif segment_name == "At Risk":
        recommendations.extend([
            "Launch immediate win-back campaigns",
            "Offer personalized discounts and incentives",
            "Conduct customer feedback surveys to understand issues"
        ])
    elif segment_name == "New Customer":
        recommendations.extend([
            "Implement onboarding email sequences",
            "Offer first-time buyer incentives for repeat purchases",
            "Provide educational content about products"
        ])
    elif avg_frequency < 2:
        recommendations.append("Focus on increasing purchase frequency with regular promotions")
    
    return recommendations


def _estimate_growth_rate(platform_data: Dict) -> float:
    """Estimate customer growth rate (placeholder implementation)"""
    # This would be calculated from historical data in a real implementation
    return 5.0  # 5% monthly growth placeholder


def _estimate_churn_trend(platform_data: Dict) -> str:
    """Estimate churn trend direction"""
    at_risk_percentage = (platform_data.get("at_risk_customers", 0) / 
                         platform_data.get("total_customers", 1)) * 100
    
    if at_risk_percentage < 20:
        return "improving"
    elif at_risk_percentage < 40:
        return "stable"
    else:
        return "concerning"


def _generate_trend_recommendations(platform_data: Dict) -> List[str]:
    """Generate recommendations based on trends"""
    recommendations = []
    
    churn_trend = _estimate_churn_trend(platform_data)
    
    if churn_trend == "concerning":
        recommendations.extend([
            "Implement proactive churn prevention strategies",
            "Analyze root causes of customer attrition",
            "Enhance customer support and engagement"
        ])
    elif churn_trend == "stable":
        recommendations.append("Monitor customer satisfaction metrics closely")
    else:
        recommendations.append("Continue current retention strategies")
    
    return recommendations

# ========== ADVANCED ML CLV ENDPOINTS ==========

@router.get("/analytics/clv/ml-predictions")
def get_ml_clv_predictions():
    """
    Get ML-powered CLV predictions with confidence intervals and feature importance
    
    Returns comprehensive analysis including:
    - Model performance metrics
    - Customer segment CLV analysis
    - Top value customer predictions
    - Actionable recommendations
    """
    try:
        results = get_advanced_clv_insights()
        
        if 'error' in results:
            return {
                "status": "fallback",
                "message": results['error'],
                "data": results
            }
        
        return {
            "status": "success",
            "message": "ML CLV predictions generated successfully",
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"ML CLV prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate ML CLV predictions: {str(e)}")

@router.get("/analytics/clv/predictive-insights")
def get_predictive_clv_insights(
    segment: Optional[str] = Query(None, description="Filter by customer segment"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    min_confidence: Optional[float] = Query(0.7, description="Minimum prediction confidence")
):
    """
    Get predictive CLV insights with filtering capabilities
    
    Parameters:
    - segment: Filter results by customer segment
    - platform: Filter results by platform  
    - min_confidence: Minimum prediction confidence threshold
    """
    try:
        predictor = AdvancedCLVPredictor()
        
        # Get comprehensive analysis
        analysis_results = predictor.analyze_customer_segments()
        
        if 'error' in analysis_results:
            return {
                "status": "error",
                "message": analysis_results['error']
            }
        
        # Apply filters if provided
        filtered_results = analysis_results.copy()
        
        if 'high_confidence_predictions' in filtered_results:
            predictions = filtered_results['high_confidence_predictions']
            
            if segment:
                predictions = [p for p in predictions if p.get('segment_name') == segment]
            
            if platform:
                predictions = [p for p in predictions if p.get('platform') == platform]
            
            if min_confidence:
                predictions = [p for p in predictions if p.get('clv_confidence', 0) >= min_confidence]
            
            filtered_results['filtered_predictions'] = predictions
            filtered_results['filter_applied'] = {
                'segment': segment,
                'platform': platform,
                'min_confidence': min_confidence,
                'results_count': len(predictions)
            }
        
        return {
            "status": "success",
            "data": filtered_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Predictive CLV insights failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate predictive insights: {str(e)}")

@router.get("/analytics/clv/model-performance")
def get_clv_model_performance():
    """
    Get detailed performance metrics of the ML CLV prediction models
    
    Returns:
    - Model accuracy metrics (MAE, RMSE, R²)
    - Feature importance rankings
    - Training data statistics
    - Model comparison results
    """
    try:
        predictor = AdvancedCLVPredictor()
        training_results = predictor.train_models()
        
        return {
            "status": "success",
            "message": "Model performance metrics retrieved successfully",
            "data": {
                "training_summary": training_results['training_summary'],
                "model_performance": training_results['model_performance'],
                "feature_importance": training_results.get('feature_importance', {}),
                "model_descriptions": {
                    "random_forest": "Ensemble of decision trees, good for non-linear patterns",
                    "gradient_boost": "Sequential boosting model, excellent for complex relationships", 
                    "linear": "Linear regression baseline, interpretable and fast"
                },
                "performance_interpretation": {
                    "mae": "Mean Absolute Error - average prediction error in currency units",
                    "rmse": "Root Mean Square Error - penalizes larger prediction errors",
                    "r2": "R-squared - proportion of variance explained by the model (higher is better)"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Model performance retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model performance: {str(e)}")

@router.post("/analytics/clv/predict-customer")
def predict_customer_clv(customer_data: dict):
    """
    Predict CLV for a specific customer using ML models
    
    Expected input format:
    {
        "frequency": 5,
        "monetary": 1250.00,
        "recency_days": 45,
        "platform": "shopify"
    }
    
    Returns prediction with confidence intervals and risk assessment
    """
    try:
        # Validate required fields
        required_fields = ['frequency', 'monetary', 'recency_days']
        for field in required_fields:
            if field not in customer_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        predictor = AdvancedCLVPredictor()
        if not predictor.is_trained:
            predictor.train_models()
        
        # Convert to DataFrame for prediction
        import pandas as pd
        df = pd.DataFrame([customer_data])
        
        # Make prediction
        prediction = predictor.predict_clv(df)
        
        # Extract single customer results
        result = {
            "predicted_clv": float(prediction['predicted_clv'][0]),
            "confidence_interval": {
                "lower": float(prediction['confidence_lower'][0]),
                "upper": float(prediction['confidence_upper'][0])
            },
            "prediction_confidence": float(prediction['prediction_confidence'][0]),
            "risk_assessment": {
                "churn_risk": "high" if customer_data['recency_days'] > 90 else "medium" if customer_data['recency_days'] > 60 else "low",
                "value_tier": "high" if customer_data['monetary'] > 1000 else "medium" if customer_data['monetary'] > 300 else "low"
            },
            "recommendations": _generate_customer_recommendations(customer_data, prediction)
        }
        
        return {
            "status": "success",
            "message": "Customer CLV predicted successfully",
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Customer CLV prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to predict customer CLV: {str(e)}")

def _generate_customer_recommendations(customer_data, prediction):
    """Generate personalized recommendations based on customer data and CLV prediction"""
    recommendations = []
    
    predicted_clv = float(prediction['predicted_clv'][0])
    confidence = float(prediction['prediction_confidence'][0])
    
    # High-value customer recommendations
    if predicted_clv > 2000:
        recommendations.append({
            "type": "retention",
            "priority": "high", 
            "action": "Enroll in VIP program with exclusive benefits",
            "reason": f"High predicted CLV of ${predicted_clv:.2f}"
        })
    
    # Frequency-based recommendations
    if customer_data['frequency'] >= 5:
        recommendations.append({
            "type": "loyalty",
            "priority": "medium",
            "action": "Offer loyalty rewards and referral bonuses",
            "reason": "High purchase frequency indicates loyalty"
        })
    
    # Recency-based recommendations  
    if customer_data['recency_days'] > 60:
        recommendations.append({
            "type": "re-engagement",
            "priority": "high",
            "action": "Launch win-back campaign with personalized offers",
            "reason": f"Customer inactive for {customer_data['recency_days']} days"
        })
    
    # Confidence-based recommendations
    if confidence < 0.6:
        recommendations.append({
            "type": "data_collection",
            "priority": "low",
            "action": "Collect more customer interaction data to improve predictions",
            "reason": f"Low prediction confidence ({confidence:.2f})"
        })
    
    return recommendations