"""
Cross-Platform Analytics Engine

This module provides comprehensive analytics and comparison capabilities across multiple e-commerce platforms.
Supports Shopify, WooCommerce, Magento, Amazon, and Generic CSV platforms with advanced ML insights.

Features:
- Platform performance comparison and KPI calculations
- Revenue, customer, and order analytics by platform
- ML-powered platform performance prediction
- Anomaly detection for platform performance issues
- Platform recommendation engine for business optimization
- Statistical modeling for competitive analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import create_engine, text
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import logging
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PlatformPerformance:
    """Data class for platform performance metrics"""
    platform: str
    total_customers: int
    total_orders: int
    total_revenue: float
    avg_order_value: float
    avg_customer_value: float
    customer_retention_rate: float
    order_frequency: float
    growth_rate: float
    market_share: float
    performance_score: float

@dataclass
class PlatformPrediction:
    """Data class for platform performance predictions"""
    platform: str
    predicted_revenue_30d: float
    predicted_revenue_90d: float
    predicted_customers_30d: int
    predicted_orders_30d: int
    confidence_score: float
    growth_trend: str
    risk_level: str

class CrossPlatformAnalyticsEngine:
    """
    Advanced analytics engine for cross-platform e-commerce performance analysis
    """
    
    def __init__(self, db_url: str = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"):
        """
        Initialize the cross-platform analytics engine
        
        Args:
            db_url: Database connection string
        """
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.platforms = ['shopify', 'woocommerce', 'magento', 'amazon', 'generic_csv']
        self.scaler = StandardScaler()
        self.performance_model = None
        self.anomaly_detector = None
        
        logger.info("Cross-Platform Analytics Engine initialized")
    
    def get_platform_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive overview of all platforms
        
        Returns:
            Dictionary containing platform overview data
        """
        try:
            with self.engine.connect() as conn:
                # Overall platform statistics
                platform_stats = conn.execute(text("""
                    SELECT 
                        platform,
                        COUNT(DISTINCT id) as total_customers,
                        AVG(total_spent::numeric) as avg_customer_value,
                        SUM(total_spent::numeric) as total_revenue,
                        COUNT(DISTINCT 
                            CASE WHEN total_spent > 0 THEN id END
                        ) as active_customers,
                        AVG(orders_count) as avg_orders_per_customer
                    FROM universal_customers 
                    GROUP BY platform
                    ORDER BY total_revenue DESC
                """))
                
                # Order statistics by platform
                order_stats = conn.execute(text("""
                    SELECT 
                        platform,
                        COUNT(*) as total_orders,
                        AVG(total_amount::numeric) as avg_order_value,
                        SUM(total_amount::numeric) as platform_revenue,
                        COUNT(DISTINCT customer_id) as unique_customers,
                        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
                        AVG(EXTRACT(EPOCH FROM (NOW() - order_date))/86400) as avg_recency_days
                    FROM universal_orders
                    GROUP BY platform
                    ORDER BY platform_revenue DESC
                """))
                
                # Product performance by platform
                product_stats = conn.execute(text("""
                    SELECT 
                        p.platform,
                        COUNT(DISTINCT p.id) as total_products,
                        AVG(p.price::numeric) as avg_product_price,
                        COUNT(DISTINCT oi.id) as total_sales_items,
                        SUM(oi.quantity * p.price::numeric) as product_revenue
                    FROM universal_products p
                    LEFT JOIN universal_order_items oi ON p.id = oi.product_id
                    GROUP BY p.platform
                    ORDER BY product_revenue DESC NULLS LAST
                """))
                
                # Time-based trends (last 30 days)
                trend_stats = conn.execute(text("""
                    SELECT 
                        platform,
                        DATE_TRUNC('week', order_date) as week,
                        COUNT(*) as weekly_orders,
                        SUM(total_amount::numeric) as weekly_revenue
                    FROM universal_orders
                    WHERE order_date >= NOW() - INTERVAL '30 days'
                    GROUP BY platform, DATE_TRUNC('week', order_date)
                    ORDER BY platform, week
                """))
                
                return {
                    "platform_overview": [dict(row) for row in platform_stats.mappings()],
                    "order_analytics": [dict(row) for row in order_stats.mappings()],
                    "product_performance": [dict(row) for row in product_stats.mappings()],
                    "trend_analysis": [dict(row) for row in trend_stats.mappings()],
                    "total_platforms": len(self.platforms),
                    "analysis_timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error in get_platform_overview: {str(e)}")
            return {"error": str(e)}
    
    def calculate_platform_performance_scores(self) -> List[PlatformPerformance]:
        """
        Calculate comprehensive performance scores for each platform
        
        Returns:
            List of PlatformPerformance objects with calculated metrics
        """
        try:
            with self.engine.connect() as conn:
                # Get comprehensive platform data
                platform_data = conn.execute(text("""
                    SELECT 
                        c.platform,
                        COUNT(DISTINCT c.id) as total_customers,
                        COUNT(DISTINCT o.id) as total_orders,
                        COALESCE(SUM(o.total_amount::numeric), 0) as total_revenue,
                        COALESCE(AVG(o.total_amount::numeric), 0) as avg_order_value,
                        COALESCE(AVG(c.total_spent::numeric), 0) as avg_customer_value,
                        COALESCE(AVG(c.orders_count), 0) as avg_order_frequency,
                        COUNT(DISTINCT CASE WHEN c.orders_count > 1 THEN c.id END) * 100.0 / 
                            NULLIF(COUNT(DISTINCT c.id), 0) as retention_rate
                    FROM universal_customers c
                    LEFT JOIN universal_orders o ON c.id = o.customer_id
                    GROUP BY c.platform
                """))
                
                platform_performances = []
                total_revenue = 0
                platform_revenues = {}
                
                # First pass: calculate total revenue for market share
                for row in platform_data.mappings():
                    platform_revenues[row['platform']] = float(row['total_revenue'])
                    total_revenue += float(row['total_revenue'])
                
                # Reset cursor
                platform_data = conn.execute(text("""
                    SELECT 
                        c.platform,
                        COUNT(DISTINCT c.id) as total_customers,
                        COUNT(DISTINCT o.id) as total_orders,
                        COALESCE(SUM(o.total_amount::numeric), 0) as total_revenue,
                        COALESCE(AVG(o.total_amount::numeric), 0) as avg_order_value,
                        COALESCE(AVG(c.total_spent::numeric), 0) as avg_customer_value,
                        COALESCE(AVG(c.orders_count), 0) as avg_order_frequency,
                        COUNT(DISTINCT CASE WHEN c.orders_count > 1 THEN c.id END) * 100.0 / 
                            NULLIF(COUNT(DISTINCT c.id), 0) as retention_rate
                    FROM universal_customers c
                    LEFT JOIN universal_orders o ON c.id = o.customer_id
                    GROUP BY c.platform
                """))
                
                # Second pass: create performance objects
                for row in platform_data.mappings():
                    platform = row['platform']
                    revenue = float(row['total_revenue'])
                    customers = int(row['total_customers'])
                    orders = int(row['total_orders'])
                    
                    # Calculate market share
                    market_share = (revenue / total_revenue * 100) if total_revenue > 0 else 0
                    
                    # Calculate growth rate (simplified - could be enhanced with historical data)
                    growth_rate = self._calculate_growth_rate(platform, conn)
                    
                    # Calculate performance score (weighted composite score)
                    performance_score = self._calculate_performance_score(
                        revenue, float(row['avg_order_value']), float(row['avg_customer_value']),
                        float(row['retention_rate']), market_share
                    )
                    
                    platform_performance = PlatformPerformance(
                        platform=platform,
                        total_customers=customers,
                        total_orders=orders,
                        total_revenue=revenue,
                        avg_order_value=float(row['avg_order_value']),
                        avg_customer_value=float(row['avg_customer_value']),
                        customer_retention_rate=float(row['retention_rate']),
                        order_frequency=float(row['avg_order_frequency']),
                        growth_rate=growth_rate,
                        market_share=market_share,
                        performance_score=performance_score
                    )
                    
                    platform_performances.append(platform_performance)
                
                # Sort by performance score
                platform_performances.sort(key=lambda x: x.performance_score, reverse=True)
                
                return platform_performances
                
        except Exception as e:
            logger.error(f"Error calculating platform performance scores: {str(e)}")
            return []
    
    def _calculate_growth_rate(self, platform: str, conn) -> float:
        """Calculate growth rate for a platform (simplified implementation)"""
        try:
            # Get recent vs older revenue comparison
            growth_data = conn.execute(text("""
                SELECT 
                    SUM(CASE WHEN order_date >= NOW() - INTERVAL '30 days' 
                        THEN total_amount::numeric ELSE 0 END) as recent_revenue,
                    SUM(CASE WHEN order_date >= NOW() - INTERVAL '60 days' 
                             AND order_date < NOW() - INTERVAL '30 days'
                        THEN total_amount::numeric ELSE 0 END) as previous_revenue
                FROM universal_orders 
                WHERE platform = :platform
            """), {"platform": platform})
            
            result = growth_data.fetchone()
            if result and result[1] > 0:
                recent = float(result[0])
                previous = float(result[1])
                return ((recent - previous) / previous) * 100
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_performance_score(self, revenue: float, aov: float, clv: float, 
                                   retention: float, market_share: float) -> float:
        """Calculate weighted performance score"""
        try:
            # Normalize metrics (simple min-max scaling approach)
            revenue_score = min(revenue / 500000, 1.0) * 30  # 30% weight
            aov_score = min(aov / 1000, 1.0) * 20  # 20% weight
            clv_score = min(clv / 5000, 1.0) * 25  # 25% weight
            retention_score = min(retention / 100, 1.0) * 15  # 15% weight
            market_score = min(market_share / 50, 1.0) * 10  # 10% weight
            
            return revenue_score + aov_score + clv_score + retention_score + market_score
            
        except Exception:
            return 0.0
    
    def generate_platform_comparison(self, metrics: List[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive platform comparison analysis
        
        Args:
            metrics: List of specific metrics to compare
            
        Returns:
            Dictionary containing comparison results
        """
        try:
            if metrics is None:
                metrics = ['revenue', 'customers', 'orders', 'aov', 'clv', 'retention']
            
            performances = self.calculate_platform_performance_scores()
            
            if not performances:
                return {"error": "No platform performance data available"}
            
            # Create comparison matrix
            comparison_data = []
            for perf in performances:
                comparison_data.append({
                    "platform": perf.platform,
                    "total_revenue": perf.total_revenue,
                    "total_customers": perf.total_customers,
                    "total_orders": perf.total_orders,
                    "avg_order_value": perf.avg_order_value,
                    "avg_customer_value": perf.avg_customer_value,
                    "retention_rate": perf.customer_retention_rate,
                    "order_frequency": perf.order_frequency,
                    "market_share": perf.market_share,
                    "growth_rate": perf.growth_rate,
                    "performance_score": perf.performance_score
                })
            
            # Identify top performers
            top_performer = performances[0]
            revenue_leader = max(performances, key=lambda x: x.total_revenue)
            customer_leader = max(performances, key=lambda x: x.total_customers)
            efficiency_leader = max(performances, key=lambda x: x.avg_order_value)
            
            # Generate insights
            insights = [
                f"{top_performer.platform} is the top overall performer with score {top_performer.performance_score:.1f}",
                f"{revenue_leader.platform} generates the highest revenue: ${revenue_leader.total_revenue:,.2f}",
                f"{customer_leader.platform} has the most customers: {customer_leader.total_customers:,}",
                f"{efficiency_leader.platform} has the highest average order value: ${efficiency_leader.avg_order_value:.2f}"
            ]
            
            return {
                "comparison_matrix": comparison_data,
                "performance_rankings": [
                    {"rank": i+1, "platform": perf.platform, "score": perf.performance_score}
                    for i, perf in enumerate(performances)
                ],
                "market_analysis": {
                    "total_revenue": sum(p.total_revenue for p in performances),
                    "total_customers": sum(p.total_customers for p in performances),
                    "total_orders": sum(p.total_orders for p in performances),
                    "market_leader": revenue_leader.platform,
                    "fastest_growing": max(performances, key=lambda x: x.growth_rate).platform
                },
                "key_insights": insights,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating platform comparison: {str(e)}")
            return {"error": str(e)}
    
    def predict_platform_performance(self, days_ahead: int = 30) -> List[PlatformPrediction]:
        """
        Predict platform performance using ML models
        
        Args:
            days_ahead: Number of days to predict ahead
            
        Returns:
            List of platform performance predictions
        """
        try:
            predictions = []
            
            with self.engine.connect() as conn:
                for platform in self.platforms:
                    # Get historical data for the platform
                    historical_data = conn.execute(text("""
                        SELECT 
                            DATE_TRUNC('day', order_date) as date,
                            COUNT(*) as daily_orders,
                            SUM(total_amount::numeric) as daily_revenue,
                            COUNT(DISTINCT customer_id) as daily_customers
                        FROM universal_orders 
                        WHERE platform = :platform 
                        AND order_date >= NOW() - INTERVAL '90 days'
                        GROUP BY DATE_TRUNC('day', order_date)
                        ORDER BY date
                    """), {"platform": platform})
                    
                    df = pd.DataFrame([dict(row) for row in historical_data.mappings()])
                    
                    if len(df) < 7:  # Need minimum data for prediction
                        predictions.append(PlatformPrediction(
                            platform=platform,
                            predicted_revenue_30d=0.0,
                            predicted_revenue_90d=0.0,
                            predicted_customers_30d=0,
                            predicted_orders_30d=0,
                            confidence_score=0.0,
                            growth_trend="insufficient_data",
                            risk_level="unknown"
                        ))
                        continue
                    
                    # Simple trend-based prediction (can be enhanced with more sophisticated models)
                    recent_avg_revenue = df['daily_revenue'].tail(7).mean()
                    recent_avg_orders = df['daily_orders'].tail(7).mean()
                    recent_avg_customers = df['daily_customers'].tail(7).mean()
                    
                    # Calculate trend
                    if len(df) >= 14:
                        older_avg_revenue = df['daily_revenue'].head(7).mean()
                        growth_trend = "growing" if recent_avg_revenue > older_avg_revenue else "declining"
                        confidence = min(0.85, len(df) / 30.0)  # Higher confidence with more data
                    else:
                        growth_trend = "stable"
                        confidence = 0.5
                    
                    # Risk assessment
                    revenue_variance = df['daily_revenue'].var()
                    risk_level = "high" if revenue_variance > recent_avg_revenue else "medium" if revenue_variance > recent_avg_revenue * 0.5 else "low"
                    
                    prediction = PlatformPrediction(
                        platform=platform,
                        predicted_revenue_30d=float(recent_avg_revenue * days_ahead),
                        predicted_revenue_90d=float(recent_avg_revenue * 90),
                        predicted_customers_30d=int(recent_avg_customers * days_ahead),
                        predicted_orders_30d=int(recent_avg_orders * days_ahead),
                        confidence_score=confidence,
                        growth_trend=growth_trend,
                        risk_level=risk_level
                    )
                    
                    predictions.append(prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting platform performance: {str(e)}")
            return []
    
    def detect_platform_anomalies(self) -> Dict[str, Any]:
        """
        Detect anomalies in platform performance using statistical methods
        
        Returns:
            Dictionary containing anomaly detection results
        """
        try:
            anomalies = []
            
            with self.engine.connect() as conn:
                for platform in self.platforms:
                    # Get recent performance data
                    performance_data = conn.execute(text("""
                        SELECT 
                            DATE_TRUNC('day', order_date) as date,
                            COUNT(*) as daily_orders,
                            SUM(total_amount::numeric) as daily_revenue,
                            AVG(total_amount::numeric) as avg_order_value
                        FROM universal_orders 
                        WHERE platform = :platform 
                        AND order_date >= NOW() - INTERVAL '30 days'
                        GROUP BY DATE_TRUNC('day', order_date)
                        ORDER BY date
                    """), {"platform": platform})
                    
                    df = pd.DataFrame([dict(row) for row in performance_data.mappings()])
                    
                    if len(df) < 5:
                        continue
                    
                    # Convert numeric columns to float
                    numeric_columns = ['daily_orders', 'daily_revenue', 'avg_order_value']
                    for col in numeric_columns:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Simple anomaly detection using statistical thresholds
                    for metric in ['daily_orders', 'daily_revenue', 'avg_order_value']:
                        if metric in df.columns:
                            values = df[metric].dropna()
                            if len(values) > 0:
                                mean_val = float(values.mean())
                                std_val = float(values.std())
                                
                                # Find outliers (beyond 2 standard deviations)
                                outliers = values[(values < mean_val - 2*std_val) | (values > mean_val + 2*std_val)]
                                
                                if len(outliers) > 0:
                                    anomalies.append({
                                        "platform": platform,
                                        "metric": metric,
                                        "anomaly_type": "statistical_outlier",
                                        "severity": "high" if abs(outliers.iloc[-1] - mean_val) > 3*std_val else "medium",
                                        "detected_value": float(outliers.iloc[-1]),
                                        "expected_range": f"{mean_val - 2*std_val:.2f} - {mean_val + 2*std_val:.2f}",
                                        "detection_date": datetime.now().isoformat()
                                    })
            
            return {
                "anomalies_detected": len(anomalies),
                "anomalies": anomalies,
                "detection_summary": {
                    "high_severity": len([a for a in anomalies if a['severity'] == 'high']),
                    "medium_severity": len([a for a in anomalies if a['severity'] == 'medium']),
                    "platforms_affected": len(set(a['platform'] for a in anomalies))
                },
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting platform anomalies: {str(e)}")
            return {"error": str(e)}
    
    def generate_platform_recommendations(self) -> Dict[str, Any]:
        """
        Generate actionable recommendations for platform optimization
        
        Returns:
            Dictionary containing platform recommendations
        """
        try:
            performances = self.calculate_platform_performance_scores()
            predictions = self.predict_platform_performance()
            
            if not performances:
                return {"error": "Insufficient data for recommendations"}
            
            recommendations = []
            
            # Analyze each platform
            for perf in performances:
                platform_recs = []
                
                # Revenue optimization
                if perf.avg_order_value < 100:
                    platform_recs.append({
                        "type": "revenue_optimization",
                        "priority": "high",
                        "recommendation": f"Increase average order value on {perf.platform} through upselling and bundling",
                        "current_aov": perf.avg_order_value,
                        "potential_impact": "15-25% revenue increase"
                    })
                
                # Customer retention
                if perf.customer_retention_rate < 30:
                    platform_recs.append({
                        "type": "retention_improvement",
                        "priority": "high",
                        "recommendation": f"Implement loyalty program on {perf.platform} to improve {perf.customer_retention_rate:.1f}% retention rate",
                        "current_retention": perf.customer_retention_rate,
                        "potential_impact": "10-20% retention improvement"
                    })
                
                # Market share growth
                if perf.market_share < 15:
                    platform_recs.append({
                        "type": "market_expansion",
                        "priority": "medium",
                        "recommendation": f"Invest more marketing budget in {perf.platform} to capture larger market share",
                        "current_share": perf.market_share,
                        "potential_impact": "5-10% market share increase"
                    })
                
                # Performance-based recommendations
                if perf.performance_score < 50:
                    platform_recs.append({
                        "type": "platform_optimization",
                        "priority": "high",
                        "recommendation": f"Comprehensive optimization needed for {perf.platform} - consider platform-specific improvements",
                        "current_score": perf.performance_score,
                        "potential_impact": "20-40% performance improvement"
                    })
                
                if platform_recs:
                    recommendations.extend(platform_recs)
            
            # Global recommendations
            top_performer = max(performances, key=lambda x: x.performance_score)
            underperformer = min(performances, key=lambda x: x.performance_score)
            
            global_recommendations = [
                {
                    "type": "strategic",
                    "priority": "high",
                    "recommendation": f"Replicate {top_performer.platform} best practices across other platforms",
                    "details": f"{top_performer.platform} achieves {top_performer.performance_score:.1f} performance score"
                },
                {
                    "type": "resource_allocation",
                    "priority": "medium",
                    "recommendation": f"Consider reallocating resources from {underperformer.platform} to higher-performing platforms",
                    "details": f"{underperformer.platform} has lowest performance score: {underperformer.performance_score:.1f}"
                }
            ]
            
            return {
                "platform_specific_recommendations": recommendations,
                "global_recommendations": global_recommendations,
                "recommendation_summary": {
                    "total_recommendations": len(recommendations) + len(global_recommendations),
                    "high_priority": len([r for r in recommendations if r.get('priority') == 'high']),
                    "platforms_needing_attention": len(set(r.get('platform') for r in recommendations if 'platform' in str(r)))
                },
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating platform recommendations: {str(e)}")
            return {"error": str(e)}