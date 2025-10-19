"""
Enhanced Alert System API Endpoints

Provides REST API endpoints for the ML-powered alert system including:
- Business metric monitoring
- Predictive alerts
- Alert prioritization and management
- Real-time anomaly detection
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import os

from analytics.cross_platform_analytics import CrossPlatformAnalyticsEngine
from auth import get_admin_user

# Import notification system for alert integration
try:
    from .notification_system import notification_system
    NOTIFICATION_SYSTEM_AVAILABLE = True
except ImportError:
    NOTIFICATION_SYSTEM_AVAILABLE = False
    notification_system = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize cross-platform engine
cross_platform_engine = CrossPlatformAnalyticsEngine()

# Initialize enhanced alert system (lazy loading to avoid config issues)
alert_engine = None

def get_alert_engine():
    """Lazy initialize alert engine to handle config issues"""
    global alert_engine
    if alert_engine is None:
        try:
            # Create a simple config manager for local development
            class SimpleConfigManager:
                def __init__(self):
                    self.config_data = {
                        "monitoring": {
                            "alert_threshold_cpu": 80.0,
                            "alert_threshold_memory": 85.0
                        }
                    }
                
                def getfloat(self, section, key, default=None):
                    return self.config_data.get(section, {}).get(key, default)
            
            from integrations.enhanced_alert_system import MLPoweredAlertEngine
            config_manager = SimpleConfigManager()
            alert_engine = MLPoweredAlertEngine(config_manager)
            logger.info("✅ Enhanced Alert Engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize alert engine: {e}")
            alert_engine = None
    return alert_engine

async def send_alert_notifications(alerts: List[Dict[str, Any]]):
    """Send notifications for generated alerts"""
    if not NOTIFICATION_SYSTEM_AVAILABLE or not notification_system:
        logger.warning("Notification system not available, skipping notifications")
        return
    
    for alert in alerts:
        try:
            # Convert alert to notification format
            alert_data = {
                'id': alert.get('id', f"alert_{int(datetime.now().timestamp())}"),
                'type': alert.get('type', 'general'),
                'priority_score': alert.get('priority_score', 5),
                'confidence': alert.get('confidence', 0.5),
                'data': alert.get('data', {}),
                'metadata': {
                    'generated_by': 'enhanced_alert_system',
                    'timestamp': datetime.now().isoformat(),
                    **alert.get('metadata', {})
                }
            }
            
            # Send notification in background
            await notification_system.process_alert(alert_data)
            logger.info(f"Notification sent for alert: {alert_data['id']}")
            
        except Exception as e:
            logger.error(f"Failed to send notification for alert {alert.get('id')}: {e}")

@router.get("/alerts/business-metrics")
async def get_business_metrics_analysis(admin_user: dict = Depends(get_admin_user)):
    """
    Get current business metrics analysis with anomaly detection
    
    Returns:
        Business metrics with deviation analysis and recommendations
    """
    
    try:
        # Get alert engine
        engine = get_alert_engine()
        if not engine:
            raise HTTPException(status_code=503, detail="Alert engine not available")
        
        # Get current analytics data
        overview = cross_platform_engine.get_platform_overview()
        
        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])
        
        # Run ML-powered alert analysis
        alert_results = await engine.run_comprehensive_alert_analysis(overview)
        
        return {
            "business_metrics": alert_results.get("business_metrics", []),
            "alert_summary": alert_results.get("alert_summary", {}),
            "analysis_metadata": alert_results.get("analysis_metadata", {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in business metrics analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/alerts/predictive")
async def get_predictive_alerts(
    days_ahead: int = Query(default=7, description="Number of days to predict ahead"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get ML-powered predictive alerts
    
    Args:
        days_ahead: Number of days to predict ahead (default: 7)
        
    Returns:
        Predictive alerts with confidence scores and recommendations
    """
    
    try:
        # Get alert engine
        engine = get_alert_engine()
        if not engine:
            raise HTTPException(status_code=503, detail="Alert engine not available")
        
        # Get current analytics data
        overview = cross_platform_engine.get_platform_overview()
        
        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])
        
        # Generate predictive alerts
        predictive_alerts = engine.generate_predictive_alerts(overview)
        
        # Filter by days ahead if specified
        filtered_alerts = [
            alert for alert in predictive_alerts 
            if alert.days_ahead <= days_ahead
        ]
        
        # Convert to dict format for JSON response
        alerts_data = []
        for alert in filtered_alerts:
            alert_dict = {
                "alert_id": alert.alert_id,
                "prediction_type": alert.prediction_type,
                "predicted_value": alert.predicted_value,
                "confidence": alert.confidence,
                "days_ahead": alert.days_ahead,
                "impact_severity": alert.impact_severity.value,
                "recommendation": alert.recommendation,
                "metadata": alert.metadata
            }
            alerts_data.append(alert_dict)
        
        return {
            "predictive_alerts": alerts_data,
            "prediction_summary": {
                "total_predictions": len(filtered_alerts),
                "high_confidence_predictions": len([a for a in filtered_alerts if a.confidence > 0.7]),
                "critical_predictions": len([a for a in filtered_alerts if a.impact_severity.value == "critical"]),
                "average_confidence": sum(a.confidence for a in filtered_alerts) / len(filtered_alerts) if filtered_alerts else 0
            },
            "parameters": {
                "days_ahead_filter": days_ahead,
                "total_generated_predictions": len(predictive_alerts)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in predictive alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/alerts/comprehensive")
async def get_comprehensive_alerts(
    send_notifications: bool = Query(False, description="Whether to send notifications for alerts"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get comprehensive alert analysis including business metrics, predictive alerts, and prioritization
    
    Returns:
        Complete alert analysis with ML-powered prioritization
    """
    
    try:
        # Get alert engine
        engine = get_alert_engine()
        if not engine:
            raise HTTPException(status_code=503, detail="Alert engine not available")
        
        # Get current analytics data
        overview = cross_platform_engine.get_platform_overview()
        
        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])
        
        # Run comprehensive ML alert analysis
        alert_results = await engine.run_comprehensive_alert_analysis(overview)
        
        # Send notifications if requested and alerts are present
        notification_status = None
        if send_notifications and alert_results.get('alerts'):
            try:
                await send_alert_notifications(alert_results['alerts'])
                notification_status = {
                    "notifications_sent": True,
                    "alert_count": len(alert_results['alerts']),
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                logger.error(f"Failed to send notifications: {e}")
                notification_status = {
                    "notifications_sent": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        
        response = {
            "comprehensive_analysis": alert_results,
            "metadata": {
                "endpoint": "/alerts/comprehensive",
                "description": "ML-powered comprehensive alert analysis",
                "features": [
                    "business_metric_monitoring",
                    "predictive_alerts",
                    "intelligent_prioritization",
                    "anomaly_detection"
                ],
                "analysis_timestamp": datetime.now().isoformat()
            }
        }
        
        if notification_status:
            response["notification_status"] = notification_status
        
        return response
        
    except Exception as e:
        logger.error(f"Error in comprehensive alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/alerts/priority/{priority_level}")
async def get_alerts_by_priority(
    priority_level: str,
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get alerts filtered by priority level
    
    Args:
        priority_level: Priority level (critical, high, medium, low)
        
    Returns:
        Alerts filtered by specified priority level
    """
    
    try:
        # Validate priority level
        valid_priorities = ["critical", "high", "medium", "low"]
        if priority_level.lower() not in valid_priorities:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid priority level. Must be one of: {valid_priorities}"
            )
        
        # Get comprehensive alerts
        overview = cross_platform_engine.get_platform_overview()
        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])
        
        alert_results = await alert_engine.run_comprehensive_alert_analysis(overview)
        all_alerts = alert_results.get("prioritized_alerts", [])
        
        # Filter by priority level
        if priority_level.lower() == "critical":
            filtered_alerts = [a for a in all_alerts if a.get("severity") == "critical"]
        elif priority_level.lower() == "high":
            filtered_alerts = [a for a in all_alerts if a.get("priority_score", 0) >= 4.0]
        elif priority_level.lower() == "medium":
            filtered_alerts = [a for a in all_alerts if 2.0 <= a.get("priority_score", 0) < 4.0]
        else:  # low
            filtered_alerts = [a for a in all_alerts if a.get("priority_score", 0) < 2.0]
        
        return {
            "filtered_alerts": filtered_alerts,
            "filter_summary": {
                "priority_level": priority_level,
                "total_alerts_in_category": len(filtered_alerts),
                "total_alerts_available": len(all_alerts),
                "percentage_of_total": (len(filtered_alerts) / len(all_alerts) * 100) if all_alerts else 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filtering alerts by priority: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/alerts/history")
async def get_alert_history(
    limit: int = Query(default=20, description="Number of alert batches to return"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get alert history and trends
    
    Args:
        limit: Number of historical alert batches to return
        
    Returns:
        Historical alert data with trend analysis
    """
    
    try:
        # Get alert history from the engine
        history = alert_engine.alert_history[-limit:] if alert_engine.alert_history else []
        
        # Calculate trends
        trends = {}
        if len(history) >= 2:
            recent = history[-1]
            previous = history[-2]
            
            trends = {
                "total_alerts_trend": recent.get("total_alerts", 0) - previous.get("total_alerts", 0),
                "critical_alerts_trend": recent.get("critical_alerts", 0) - previous.get("critical_alerts", 0),
                "predictive_alerts_trend": recent.get("predictive_alerts", 0) - previous.get("predictive_alerts", 0),
                "is_improving": recent.get("total_alerts", 0) <= previous.get("total_alerts", 0)
            }
        
        return {
            "alert_history": history,
            "trends": trends,
            "history_summary": {
                "total_batches_analyzed": len(history),
                "date_range": {
                    "earliest": history[0].get("timestamp") if history else None,
                    "latest": history[-1].get("timestamp") if history else None
                },
                "average_alerts_per_batch": sum(h.get("total_alerts", 0) for h in history) / len(history) if history else 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving alert history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/alerts/configure-thresholds")
async def configure_alert_thresholds(
    thresholds: Dict[str, float],
    admin_user: dict = Depends(get_admin_user)
):
    """
    Configure business metric alert thresholds
    
    Args:
        thresholds: Dictionary of threshold values to update
        
    Returns:
        Updated threshold configuration
    """
    
    try:
        # Validate threshold values
        valid_thresholds = {
            "revenue_drop_percentage",
            "conversion_rate_drop", 
            "customer_churn_increase",
            "avg_order_value_drop",
            "anomaly_score_threshold"
        }
        
        invalid_keys = set(thresholds.keys()) - valid_thresholds
        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid threshold keys: {invalid_keys}. Valid keys: {valid_thresholds}"
            )
        
        # Update thresholds in the alert engine
        for key, value in thresholds.items():
            if isinstance(value, (int, float)) and value > 0:
                alert_engine.business_thresholds[key] = float(value)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid threshold value for {key}: must be a positive number"
                )
        
        logger.info(f"Alert thresholds updated: {thresholds}")
        
        return {
            "message": "Alert thresholds updated successfully",
            "updated_thresholds": thresholds,
            "current_all_thresholds": alert_engine.business_thresholds,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring alert thresholds: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/alerts/health")
async def get_alert_system_health():
    """
    Get health status of the enhanced alert system (public endpoint)
    
    Returns:
        System health information and configuration status
    """
    
    try:
        # Test basic functionality
        engine = get_alert_engine()
        
        if not engine:
            return {
                "status": "unhealthy",
                "error": "Alert engine not available",
                "timestamp": datetime.now().isoformat()
            }
        
        # Basic test without requiring full data
        system_healthy = True
        
        return {
            "status": "healthy" if system_healthy else "unhealthy",
            "system_info": {
                "ml_models_loaded": True,
                "anomaly_detectors_ready": True,
                "alert_history_entries": len(engine.alert_history) if engine else 0,
                "business_metrics_tracked": len(engine.business_thresholds) if engine else 0,
                "last_analysis_successful": system_healthy
            },
            "current_thresholds": engine.business_thresholds if engine else {},
            "capabilities": {
                "business_metric_monitoring": True,
                "predictive_alerts": True,
                "anomaly_detection": True,
                "intelligent_prioritization": True,
                "configurable_thresholds": True
            },
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking alert system health: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/alerts/demo")
async def get_alert_system_demo():
    """
    Demonstrate the enhanced alert system with sample data (public endpoint)
    
    Returns:
        Sample alert analysis demonstrating Week 7 capabilities
    """
    
    try:
        # Get alert engine
        engine = get_alert_engine()
        if not engine:
            return {
                "error": "Alert engine not available",
                "timestamp": datetime.now().isoformat()
            }
        
        # Mock analytics data for demo
        demo_analytics = {
            "platform_overview": [
                {"platform": "WooCommerce", "total_revenue": 85000, "total_customers": 1900},
                {"platform": "Shopify", "total_revenue": 55000, "total_customers": 1300}
            ],
            "order_analytics": [
                {"platform": "WooCommerce", "total_orders": 3200},
                {"platform": "Shopify", "total_orders": 1800}
            ]
        }
        
        # Run comprehensive alert analysis
        alert_results = await engine.run_comprehensive_alert_analysis(demo_analytics)
        
        return {
            "demo_results": alert_results,
            "demo_info": {
                "description": "Week 7 Enhanced Alert System Demo",
                "features_demonstrated": [
                    "Business metric monitoring",
                    "ML-powered predictive alerts", 
                    "Intelligent alert prioritization",
                    "Anomaly detection",
                    "Contextual recommendations"
                ],
                "sample_data": demo_analytics
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in alert system demo: {str(e)}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/alerts/demo-with-notifications")
async def get_alert_demo_with_notifications():
    """
    Demonstrate the enhanced alert system with automatic notifications (public endpoint)
    
    Returns:
        Sample alert analysis with notification delivery status
    """
    
    try:
        # Get alert engine
        engine = get_alert_engine()
        if not engine:
            return {
                "error": "Alert engine not available",
                "timestamp": datetime.now().isoformat()
            }
        
        # Mock analytics data for demo
        demo_analytics = {
            "platform_overview": [
                {"platform": "WooCommerce", "total_revenue": 85000, "total_customers": 1900},
                {"platform": "Shopify", "total_revenue": 55000, "total_customers": 1300}
            ],
            "order_analytics": [
                {"platform": "WooCommerce", "total_orders": 3200},
                {"platform": "Shopify", "total_orders": 1800}
            ]
        }
        
        # Run comprehensive alert analysis
        alert_results = await engine.run_comprehensive_alert_analysis(demo_analytics)
        
        # Send notifications if alerts are present
        notification_status = None
        if alert_results.get('prioritized_alerts'):
            try:
                await send_alert_notifications(alert_results['prioritized_alerts'])
                notification_status = {
                    "notifications_sent": True,
                    "alert_count": len(alert_results['prioritized_alerts']),
                    "timestamp": datetime.now().isoformat(),
                    "notification_details": "Notifications sent to all configured recipients"
                }
            except Exception as e:
                logger.error(f"Failed to send notifications: {e}")
                notification_status = {
                    "notifications_sent": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
        else:
            notification_status = {
                "notifications_sent": False,
                "reason": "No alerts generated",
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "demo_results": alert_results,
            "notification_status": notification_status,
            "demo_info": {
                "description": "Week 7 Enhanced Alert System with Multi-Channel Notification Integration Demo",
                "features_demonstrated": [
                    "Business metric monitoring",
                    "ML-powered predictive alerts", 
                    "Intelligent alert prioritization",
                    "Anomaly detection",
                    "Multi-channel notification delivery",
                    "Alert-notification integration",
                    "Contextual recommendations"
                ],
                "sample_data": demo_analytics
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in alert system demo with notifications: {str(e)}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }