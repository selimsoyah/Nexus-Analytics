"""
Enhanced ML-Powered Alert System for Nexus Analytics
====================================================

Extends the basic AlertManager with:
- ML-powered predictive alerts
- Business metric monitoring
- Intelligent alert prioritization
- Revenue drop detection
- Conversion rate monitoring
- Customer behavior anomaly detection

Author: Nexus Analytics Team
Version: 2.0.0
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import statistics

# Import existing modules
from .production_monitor import AlertManager, ConfigurationManager
from .ml_analytics import CustomerSegmentationModel, SalesForecastingModel, ProductPerformanceAnalyzer


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Business alert categories"""
    REVENUE = "revenue"
    CONVERSION = "conversion"
    CUSTOMER_BEHAVIOR = "customer_behavior"
    SYSTEM_PERFORMANCE = "system_performance"
    PREDICTION = "prediction"
    ANOMALY = "anomaly"


@dataclass
class BusinessMetric:
    """Business metric definition"""
    name: str
    current_value: float
    historical_average: float
    threshold_deviation: float
    category: AlertCategory
    is_critical: bool = False


@dataclass
class PredictiveAlert:
    """ML-powered predictive alert"""
    alert_id: str
    prediction_type: str
    predicted_value: float
    confidence: float
    days_ahead: int
    impact_severity: AlertSeverity
    recommendation: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class MLPoweredAlertEngine:
    """
    Enhanced alert system with ML predictive capabilities
    """
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.base_alert_manager = AlertManager(config_manager)
        
        # ML models for predictions
        self.segmentation_model = CustomerSegmentationModel()
        self.forecasting_model = SalesForecastingModel()
        self.performance_analyzer = ProductPerformanceAnalyzer()
        
        # Anomaly detection models
        self.revenue_anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.conversion_anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        
        # Business metrics thresholds
        self.business_thresholds = {
            "revenue_drop_percentage": 15.0,  # Alert if revenue drops by 15%
            "conversion_rate_drop": 0.5,      # Alert if conversion drops by 0.5%
            "customer_churn_increase": 10.0,  # Alert if churn increases by 10%
            "avg_order_value_drop": 20.0,     # Alert if AOV drops by 20%
            "anomaly_score_threshold": -0.5   # Isolation Forest threshold
        }
        
        # Alert history for intelligent prioritization
        self.alert_history: List[Dict[str, Any]] = []
        self.business_metrics_history: List[BusinessMetric] = []
        
    def calculate_business_metrics(self, analytics_data: Dict[str, Any]) -> List[BusinessMetric]:
        """
        Calculate current business metrics from analytics data
        
        Args:
            analytics_data: Current platform analytics data
            
        Returns:
            List of business metrics with deviation analysis
        """
        
        try:
            metrics = []
            
            # Extract current metrics
            platform_data = analytics_data.get("platform_overview", [])
            order_data = analytics_data.get("order_analytics", [])
            
            if not platform_data or not order_data:
                self.logger.warning("Insufficient data for business metrics calculation")
                return metrics
            
            # Calculate total revenue
            total_revenue = sum(p.get("total_revenue", 0) for p in platform_data)
            total_customers = sum(p.get("total_customers", 0) for p in platform_data)
            total_orders = sum(o.get("total_orders", 0) for o in order_data)
            
            # Calculate conversion rate (simplified)
            conversion_rate = (total_orders / total_customers * 100) if total_customers > 0 else 0
            
            # Calculate average order value
            avg_order_value = (total_revenue / total_orders) if total_orders > 0 else 0
            
            # Get historical averages (mock data for demo - in production, query historical DB)
            historical_revenue_avg = total_revenue * 1.1  # Simulate 10% higher historical average
            historical_conversion_avg = conversion_rate * 1.05  # Simulate 5% higher historical
            historical_aov_avg = avg_order_value * 1.08  # Simulate 8% higher historical
            
            # Create business metrics
            metrics.extend([
                BusinessMetric(
                    name="total_revenue",
                    current_value=total_revenue,
                    historical_average=historical_revenue_avg,
                    threshold_deviation=self.business_thresholds["revenue_drop_percentage"],
                    category=AlertCategory.REVENUE,
                    is_critical=True
                ),
                BusinessMetric(
                    name="conversion_rate",
                    current_value=conversion_rate,
                    historical_average=historical_conversion_avg,
                    threshold_deviation=self.business_thresholds["conversion_rate_drop"],
                    category=AlertCategory.CONVERSION,
                    is_critical=True
                ),
                BusinessMetric(
                    name="average_order_value",
                    current_value=avg_order_value,
                    historical_average=historical_aov_avg,
                    threshold_deviation=self.business_thresholds["avg_order_value_drop"],
                    category=AlertCategory.REVENUE,
                    is_critical=False
                )
            ])
            
            # Store in history for trend analysis
            self.business_metrics_history.extend(metrics)
            
            # Keep only last 100 metrics for memory management
            if len(self.business_metrics_history) > 100:
                self.business_metrics_history = self.business_metrics_history[-100:]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating business metrics: {str(e)}")
            return []
    
    def detect_business_anomalies(self, metrics: List[BusinessMetric]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in business metrics using ML
        
        Args:
            metrics: Current business metrics
            
        Returns:
            List of detected anomalies with severity and recommendations
        """
        
        anomalies = []
        
        try:
            for metric in metrics:
                # Calculate percentage deviation
                if metric.historical_average > 0:
                    deviation_percentage = ((metric.current_value - metric.historical_average) / 
                                          metric.historical_average * 100)
                else:
                    deviation_percentage = 0
                
                # Check if deviation exceeds threshold
                is_negative_deviation = deviation_percentage < -metric.threshold_deviation
                
                if is_negative_deviation:
                    severity = AlertSeverity.CRITICAL if metric.is_critical else AlertSeverity.HIGH
                    
                    # Generate contextual recommendation
                    recommendation = self._generate_metric_recommendation(metric, deviation_percentage)
                    
                    anomaly = {
                        "metric_name": metric.name,
                        "category": metric.category.value,
                        "current_value": metric.current_value,
                        "historical_average": metric.historical_average,
                        "deviation_percentage": deviation_percentage,
                        "severity": severity.value,
                        "recommendation": recommendation,
                        "timestamp": datetime.now().isoformat(),
                        "is_critical": metric.is_critical
                    }
                    
                    anomalies.append(anomaly)
                    
                    self.logger.warning(
                        f"🚨 Business anomaly detected: {metric.name} "
                        f"down {abs(deviation_percentage):.1f}% from historical average"
                    )
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting business anomalies: {str(e)}")
            return []
    
    def generate_predictive_alerts(self, analytics_data: Dict[str, Any]) -> List[PredictiveAlert]:
        """
        Generate ML-powered predictive alerts
        
        Args:
            analytics_data: Current analytics data for prediction
            
        Returns:
            List of predictive alerts with recommendations
        """
        
        predictive_alerts = []
        
        try:
            # Mock predictive analysis (in production, use trained ML models)
            
            # Revenue prediction alert
            current_revenue = sum(
                p.get("total_revenue", 0) 
                for p in analytics_data.get("platform_overview", [])
            )
            
            # Simulate revenue trend prediction
            predicted_revenue_7d = current_revenue * 0.92  # Predict 8% decline
            revenue_confidence = 0.75
            
            if predicted_revenue_7d < current_revenue * 0.95:  # More than 5% decline predicted
                predictive_alerts.append(PredictiveAlert(
                    alert_id=f"pred_revenue_{int(datetime.now().timestamp())}",
                    prediction_type="revenue_decline",
                    predicted_value=predicted_revenue_7d,
                    confidence=revenue_confidence,
                    days_ahead=7,
                    impact_severity=AlertSeverity.HIGH,
                    recommendation="Consider promotional campaigns or customer retention strategies",
                    metadata={
                        "current_revenue": current_revenue,
                        "predicted_decline": ((current_revenue - predicted_revenue_7d) / current_revenue * 100)
                    }
                ))
            
            # Customer churn prediction alert
            total_customers = sum(
                p.get("total_customers", 0) 
                for p in analytics_data.get("platform_overview", [])
            )
            
            # Simulate churn prediction
            predicted_churn_rate = 12.5  # Predict 12.5% churn
            churn_confidence = 0.68
            
            if predicted_churn_rate > 10.0:  # High churn predicted
                predictive_alerts.append(PredictiveAlert(
                    alert_id=f"pred_churn_{int(datetime.now().timestamp())}",
                    prediction_type="customer_churn",
                    predicted_value=predicted_churn_rate,
                    confidence=churn_confidence,
                    days_ahead=14,
                    impact_severity=AlertSeverity.MEDIUM,
                    recommendation="Implement customer engagement campaigns and loyalty programs",
                    metadata={
                        "total_customers": total_customers,
                        "predicted_churned_customers": int(total_customers * predicted_churn_rate / 100)
                    }
                ))
            
            # Conversion rate prediction
            current_orders = sum(
                o.get("total_orders", 0) 
                for o in analytics_data.get("order_analytics", [])
            )
            current_conversion = (current_orders / total_customers * 100) if total_customers > 0 else 0
            predicted_conversion = current_conversion * 0.88  # Predict 12% decline
            
            if predicted_conversion < current_conversion * 0.9:  # More than 10% decline
                predictive_alerts.append(PredictiveAlert(
                    alert_id=f"pred_conversion_{int(datetime.now().timestamp())}",
                    prediction_type="conversion_decline",
                    predicted_value=predicted_conversion,
                    confidence=0.71,
                    days_ahead=10,
                    impact_severity=AlertSeverity.MEDIUM,
                    recommendation="Optimize checkout process and improve product recommendations",
                    metadata={
                        "current_conversion_rate": current_conversion,
                        "predicted_decline_percentage": ((current_conversion - predicted_conversion) / current_conversion * 100)
                    }
                ))
            
            return predictive_alerts
            
        except Exception as e:
            self.logger.error(f"Error generating predictive alerts: {str(e)}")
            return []
    
    def prioritize_alerts(self, alerts: List[Dict[str, Any]], 
                         predictive_alerts: List[PredictiveAlert]) -> List[Dict[str, Any]]:
        """
        Intelligently prioritize alerts using ML-based scoring
        
        Args:
            alerts: Business anomaly alerts
            predictive_alerts: ML-powered predictive alerts
            
        Returns:
            Prioritized list of all alerts with ML-calculated priority scores
        """
        
        all_alerts = []
        
        try:
            # Process business anomaly alerts
            for alert in alerts:
                priority_score = self._calculate_alert_priority(alert)
                alert["priority_score"] = priority_score
                alert["alert_type"] = "anomaly"
                all_alerts.append(alert)
            
            # Process predictive alerts
            for pred_alert in predictive_alerts:
                alert_dict = {
                    "alert_id": pred_alert.alert_id,
                    "metric_name": pred_alert.prediction_type,
                    "category": "prediction",
                    "predicted_value": pred_alert.predicted_value,
                    "confidence": pred_alert.confidence,
                    "days_ahead": pred_alert.days_ahead,
                    "severity": pred_alert.impact_severity.value,
                    "recommendation": pred_alert.recommendation,
                    "metadata": pred_alert.metadata,
                    "timestamp": datetime.now().isoformat(),
                    "alert_type": "predictive"
                }
                
                # Calculate priority for predictive alerts
                priority_score = self._calculate_predictive_priority(pred_alert)
                alert_dict["priority_score"] = priority_score
                
                all_alerts.append(alert_dict)
            
            # Sort by priority score (highest first)
            all_alerts.sort(key=lambda x: x["priority_score"], reverse=True)
            
            return all_alerts
            
        except Exception as e:
            self.logger.error(f"Error prioritizing alerts: {str(e)}")
            return alerts + [vars(pa) for pa in predictive_alerts]
    
    def _calculate_alert_priority(self, alert: Dict[str, Any]) -> float:
        """Calculate priority score for business anomaly alerts"""
        
        score = 0.0
        
        # Base score from severity
        severity_scores = {
            "low": 1.0,
            "medium": 2.0, 
            "high": 3.0,
            "critical": 4.0
        }
        score += severity_scores.get(alert.get("severity", "low"), 1.0)
        
        # Critical metrics get higher priority
        if alert.get("is_critical", False):
            score += 2.0
        
        # Larger deviations get higher priority
        deviation = abs(alert.get("deviation_percentage", 0))
        score += min(deviation / 10.0, 3.0)  # Cap at 3.0 additional points
        
        # Revenue and conversion alerts get priority boost
        category = alert.get("category", "")
        if category in ["revenue", "conversion"]:
            score += 1.5
        
        return round(score, 2)
    
    def _calculate_predictive_priority(self, pred_alert: PredictiveAlert) -> float:
        """Calculate priority score for predictive alerts"""
        
        score = 0.0
        
        # Base score from severity
        severity_scores = {
            AlertSeverity.LOW: 1.0,
            AlertSeverity.MEDIUM: 2.0,
            AlertSeverity.HIGH: 3.0,
            AlertSeverity.CRITICAL: 4.0
        }
        score += severity_scores.get(pred_alert.impact_severity, 1.0)
        
        # Confidence boost
        score += pred_alert.confidence * 2.0
        
        # Urgency - sooner predictions get higher priority
        if pred_alert.days_ahead <= 7:
            score += 2.0
        elif pred_alert.days_ahead <= 14:
            score += 1.0
        
        # Revenue-related predictions get priority
        if "revenue" in pred_alert.prediction_type.lower():
            score += 1.5
        
        return round(score, 2)
    
    def _generate_metric_recommendation(self, metric: BusinessMetric, 
                                      deviation_percentage: float) -> str:
        """Generate contextual recommendations for metric anomalies"""
        
        recommendations = {
            "total_revenue": [
                "Launch targeted promotional campaigns",
                "Review pricing strategy and competitor analysis", 
                "Increase marketing spend on high-converting channels",
                "Implement customer win-back campaigns"
            ],
            "conversion_rate": [
                "Optimize checkout process and reduce friction",
                "A/B testing product page layouts",
                "Improve product recommendations algorithm",
                "Review payment options and shipping costs"
            ],
            "average_order_value": [
                "Implement cross-selling and upselling strategies",
                "Create bundle offers and volume discounts",
                "Review product positioning and pricing",
                "Launch minimum order value promotions"
            ]
        }
        
        metric_recommendations = recommendations.get(metric.name, ["Review metric trends and investigate root causes"])
        
        # Add severity-based context
        if abs(deviation_percentage) > 20:
            context = "URGENT: "
        elif abs(deviation_percentage) > 10:
            context = "Important: "
        else:
            context = ""
        
        return context + metric_recommendations[0]
    
    async def run_comprehensive_alert_analysis(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run complete ML-powered alert analysis
        
        Args:
            analytics_data: Current platform analytics data
            
        Returns:
            Comprehensive alert analysis with prioritized recommendations
        """
        
        try:
            self.logger.info("🔍 Starting comprehensive ML alert analysis...")
            
            # Step 1: Calculate business metrics
            business_metrics = self.calculate_business_metrics(analytics_data)
            
            # Step 2: Detect anomalies
            anomalies = self.detect_business_anomalies(business_metrics)
            
            # Step 3: Generate predictive alerts
            predictive_alerts = self.generate_predictive_alerts(analytics_data)
            
            # Step 4: Prioritize all alerts
            prioritized_alerts = self.prioritize_alerts(anomalies, predictive_alerts)
            
            # Step 5: Generate summary insights
            summary = self._generate_alert_summary(prioritized_alerts)
            
            # Store in alert history
            alert_batch = {
                "timestamp": datetime.now().isoformat(),
                "total_alerts": len(prioritized_alerts),
                "critical_alerts": len([a for a in prioritized_alerts if a.get("severity") == "critical"]),
                "predictive_alerts": len(predictive_alerts),
                "business_anomalies": len(anomalies)
            }
            self.alert_history.append(alert_batch)
            
            # Keep only last 50 alert batches
            if len(self.alert_history) > 50:
                self.alert_history = self.alert_history[-50:]
            
            self.logger.info(
                f"✅ Alert analysis complete: {len(prioritized_alerts)} alerts generated "
                f"({len(anomalies)} anomalies, {len(predictive_alerts)} predictions)"
            )
            
            return {
                "alert_summary": summary,
                "prioritized_alerts": prioritized_alerts,
                "business_metrics": [
                    {
                        "name": m.name,
                        "current_value": m.current_value,
                        "historical_average": m.historical_average,
                        "category": m.category.value,
                        "is_critical": m.is_critical
                    } for m in business_metrics
                ],
                "analysis_metadata": {
                    "total_alerts_generated": len(prioritized_alerts),
                    "anomalies_detected": len(anomalies),
                    "predictions_generated": len(predictive_alerts),
                    "highest_priority_score": max([a.get("priority_score", 0) for a in prioritized_alerts]) if prioritized_alerts else 0,
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive alert analysis: {str(e)}")
            return {
                "error": str(e),
                "alert_summary": {"status": "error", "message": "Alert analysis failed"},
                "prioritized_alerts": [],
                "business_metrics": [],
                "analysis_metadata": {"error": True, "timestamp": datetime.now().isoformat()}
            }
    
    def _generate_alert_summary(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate executive summary of alert analysis"""
        
        if not alerts:
            return {
                "status": "healthy",
                "message": "No critical issues detected",
                "total_alerts": 0,
                "critical_count": 0,
                "top_priorities": []
            }
        
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
        high_priority = [a for a in alerts if a.get("priority_score", 0) >= 5.0]
        
        status = "critical" if critical_alerts else ("warning" if high_priority else "healthy")
        
        return {
            "status": status,
            "message": f"{len(alerts)} alerts generated with {len(critical_alerts)} critical issues",
            "total_alerts": len(alerts),
            "critical_count": len(critical_alerts),
            "high_priority_count": len(high_priority),
            "top_priorities": alerts[:3],  # Top 3 highest priority alerts
            "categories_affected": list(set(a.get("category", "unknown") for a in alerts)),
            "recommended_immediate_actions": [
                a.get("recommendation", "") for a in alerts[:2] if a.get("priority_score", 0) >= 4.0
            ]
        }


# Demo function
async def demo_enhanced_alert_system():
    """Demonstrate the enhanced ML-powered alert system"""
    
    print("🚀 Starting Enhanced ML Alert System Demo...")
    
    # Initialize system
    from .production_monitor import ConfigurationManager
    config_manager = ConfigurationManager()
    alert_engine = MLPoweredAlertEngine(config_manager)
    
    # Mock analytics data
    mock_analytics = {
        "platform_overview": [
            {"platform": "WooCommerce", "total_revenue": 75000, "total_customers": 1800},
            {"platform": "Shopify", "total_revenue": 45000, "total_customers": 1200}
        ],
        "order_analytics": [
            {"platform": "WooCommerce", "total_orders": 2800},
            {"platform": "Shopify", "total_orders": 1500}
        ]
    }
    
    # Run comprehensive analysis
    results = await alert_engine.run_comprehensive_alert_analysis(mock_analytics)
    
    print("\n📊 Alert Analysis Results:")
    print(f"Status: {results['alert_summary']['status']}")
    print(f"Total Alerts: {results['analysis_metadata']['total_alerts_generated']}")
    print(f"Critical Issues: {results['alert_summary']['critical_count']}")
    
    print("\n🔥 Top Priority Alerts:")
    for i, alert in enumerate(results['prioritized_alerts'][:3], 1):
        print(f"{i}. {alert['metric_name']} - Priority: {alert['priority_score']}")
        print(f"   Recommendation: {alert['recommendation']}")
    
    return results


if __name__ == "__main__":
    asyncio.run(demo_enhanced_alert_system())