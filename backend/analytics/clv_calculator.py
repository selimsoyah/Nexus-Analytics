"""
Customer Lifetime Value (CLV) Calculator

This module provides comprehensive CLV calculations using both traditional formulas
and advanced machine learning approaches for the Nexus Analytics platform.

Traditional CLV Formula: CLV = Average Order Value × Purchase Frequency × Customer Lifespan
Enhanced with confidence intervals, platform-specific adjustments, and ML predictions.
"""

from sqlalchemy import create_engine, text
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CLVMetrics:
    """Data class for CLV calculation metrics"""
    customer_id: str
    platform: str
    avg_order_value: float
    purchase_frequency: float
    customer_lifespan_days: int
    predicted_lifespan_days: int
    traditional_clv: float
    confidence_interval_low: float
    confidence_interval_high: float
    risk_score: float  # 0-1, probability of churn
    segment: str
    last_order_date: Optional[datetime]
    total_orders: int
    total_spent: float
    days_since_last_order: int

class CLVCalculator:
    """
    Comprehensive Customer Lifetime Value calculator supporting multiple platforms
    """
    
    def __init__(self, db_url: str = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"):
        self.engine = create_engine(db_url)
        
    def calculate_basic_clv(self, customer_external_id: str, platform: Optional[str] = None) -> CLVMetrics:
        """
        Calculate basic CLV using traditional formula with enhanced metrics
        
        Args:
            customer_external_id: External customer ID from platform
            platform: Platform identifier (optional)
            
        Returns:
            CLVMetrics object with comprehensive CLV data
        """
        
        # Get customer data with order history
        customer_data = self._get_customer_data(customer_external_id, platform)
        
        if not customer_data:
            raise ValueError(f"Customer {customer_external_id} not found")
        
        # Calculate core metrics
        avg_order_value = self._calculate_avg_order_value(customer_data)
        purchase_frequency = self._calculate_purchase_frequency(customer_data)
        customer_lifespan = self._calculate_customer_lifespan(customer_data)
        
        # Traditional CLV calculation
        traditional_clv = avg_order_value * purchase_frequency * (customer_lifespan / 365.25)
        
        # Calculate confidence intervals based on order volatility
        confidence_low, confidence_high = self._calculate_confidence_intervals(
            customer_data, traditional_clv
        )
        
        # Risk assessment
        risk_score = self._calculate_churn_risk(customer_data)
        
        # Customer segmentation
        segment = self._determine_segment(traditional_clv, customer_data)
        
        return CLVMetrics(
            customer_id=customer_external_id,
            platform=customer_data['platform'],
            avg_order_value=avg_order_value,
            purchase_frequency=purchase_frequency,
            customer_lifespan_days=customer_lifespan,
            predicted_lifespan_days=customer_lifespan,  # Same as basic for now
            traditional_clv=traditional_clv,
            confidence_interval_low=confidence_low,
            confidence_interval_high=confidence_high,
            risk_score=risk_score,
            segment=segment,
            last_order_date=customer_data.get('last_order_date'),
            total_orders=customer_data.get('total_orders', 0),
            total_spent=customer_data.get('total_spent', 0),
            days_since_last_order=customer_data.get('days_since_last_order', 0)
        )
    
    def calculate_bulk_clv(self, platform: Optional[str] = None, limit: int = 1000) -> List[CLVMetrics]:
        """
        Calculate CLV for multiple customers in bulk
        
        Args:
            platform: Filter by platform (optional)
            limit: Maximum number of customers to process
            
        Returns:
            List of CLVMetrics objects
        """
        
        # Get customer list
        customers = self._get_customer_list(platform, limit)
        clv_results = []
        
        logger.info(f"Calculating CLV for {len(customers)} customers")
        
        for customer in customers:
            try:
                clv_metrics = self.calculate_basic_clv(
                    customer['external_id'], 
                    customer['platform']
                )
                clv_results.append(clv_metrics)
                
            except Exception as e:
                logger.warning(f"CLV calculation failed for customer {customer['external_id']}: {str(e)}")
                continue
        
        logger.info(f"Successfully calculated CLV for {len(clv_results)} customers")
        return clv_results
    
    def get_platform_clv_summary(self, platform: Optional[str] = None) -> Dict:
        """
        Get CLV summary statistics by platform
        
        Args:
            platform: Platform to analyze (optional, returns all if None)
            
        Returns:
            Dictionary with platform CLV summaries
        """
        
        query = """
        SELECT 
            c.platform,
            COUNT(DISTINCT c.id) as total_customers,
            AVG(c.total_spent) as avg_total_spent,
            AVG(c.orders_count) as avg_orders,
            AVG(c.average_order_value) as avg_order_value,
            
            -- Calculate basic CLV components
            AVG(c.average_order_value * 
                (c.orders_count / GREATEST(
                    CASE 
                        WHEN c.platform_created_at IS NOT NULL 
                        THEN (CURRENT_DATE - c.platform_created_at::date) / 365.25
                        ELSE 1.0
                    END, 
                    0.1
                ))
            ) as estimated_clv,
            
            -- Customer lifecycle metrics
            AVG(
                CASE 
                    WHEN c.last_order_date IS NOT NULL 
                    THEN (CURRENT_DATE - c.last_order_date::date) 
                    ELSE 0 
                END
            ) as avg_days_since_last_order,
            AVG(
                CASE 
                    WHEN c.last_order_date IS NOT NULL AND c.platform_created_at IS NOT NULL
                    THEN (c.last_order_date::date - c.platform_created_at::date)
                    ELSE 0
                END
            ) as avg_customer_lifespan_days,
            
            -- Risk indicators
            COUNT(CASE WHEN c.last_order_date < CURRENT_DATE - INTERVAL '90 days' THEN 1 END) as at_risk_customers,
            COUNT(CASE WHEN c.orders_count = 1 THEN 1 END) as one_time_customers
            
        FROM universal_customers c
        WHERE c.orders_count > 0
        """
        
        params = {}
        if platform:
            query += " AND c.platform = :platform"
            params["platform"] = platform
            
        query += " GROUP BY c.platform ORDER BY estimated_clv DESC"
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                rows = result.fetchall()
                
                summaries = []
                for row in rows:
                    summary = {
                        "platform": row[0],
                        "total_customers": row[1],
                        "avg_total_spent": float(row[2] or 0),
                        "avg_orders": float(row[3] or 0),
                        "avg_order_value": float(row[4] or 0),
                        "estimated_avg_clv": float(row[5] or 0),
                        "avg_days_since_last_order": float(row[6] or 0),
                        "avg_customer_lifespan_days": float(row[7] or 0),
                        "at_risk_customers": row[8],
                        "one_time_customers": row[9],
                        "retention_rate": ((row[1] - row[9]) / row[1] * 100) if row[1] > 0 else 0
                    }
                    summaries.append(summary)
                
                return {
                    "platform_summaries": summaries,
                    "total_platforms": len(summaries),
                    "analysis_date": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Platform CLV summary calculation failed: {str(e)}")
            raise
    
    def _get_customer_data(self, customer_external_id: str, platform: Optional[str] = None) -> Dict:
        """Get comprehensive customer data for CLV calculation"""
        
        query = """
        SELECT 
            c.external_id,
            c.platform,
            c.total_spent,
            c.orders_count,
            c.average_order_value,
            c.last_order_date,
            c.platform_created_at,
            
            -- Order details for frequency calculation
            ARRAY_AGG(o.order_date ORDER BY o.order_date) as order_dates,
            ARRAY_AGG(o.total_amount ORDER BY o.order_date) as order_amounts,
            
            -- Calculate days since last order
            CASE 
                WHEN c.last_order_date IS NOT NULL 
                THEN (CURRENT_DATE - c.last_order_date::date)
                ELSE 0
            END as days_since_last_order
            
        FROM universal_customers c
        LEFT JOIN universal_orders o ON c.id = o.customer_id
        WHERE c.external_id = :customer_id
        """
        
        params = {"customer_id": customer_external_id}
        if platform:
            query += " AND c.platform = :platform"
            params["platform"] = platform
            
        query += " GROUP BY c.id"
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                row = result.fetchone()
                
                if not row:
                    return None
                
                return {
                    "external_id": row[0],
                    "platform": row[1],
                    "total_spent": float(row[2] or 0),
                    "total_orders": row[3] or 0,
                    "average_order_value": float(row[4] or 0),
                    "last_order_date": row[5],
                    "platform_created_at": row[6],
                    "order_dates": row[7] or [],
                    "order_amounts": [float(amt) for amt in (row[8] or [])],
                    "days_since_last_order": int(row[9] or 0)
                }
                
        except Exception as e:
            logger.error(f"Failed to get customer data: {str(e)}")
            raise
    
    def _calculate_avg_order_value(self, customer_data: Dict) -> float:
        """Calculate average order value with volatility adjustment"""
        
        if customer_data["order_amounts"]:
            amounts = customer_data["order_amounts"]
            # Use median for more robust average with outlier protection
            return float(np.median(amounts))
        
        return customer_data["average_order_value"]
    
    def _calculate_purchase_frequency(self, customer_data: Dict) -> float:
        """Calculate purchase frequency (orders per year)"""
        
        if len(customer_data["order_dates"]) < 2:
            return 1.0  # Assume annual frequency for single purchases
        
        order_dates = customer_data["order_dates"]
        first_order = min(order_dates)
        last_order = max(order_dates)
        
        # Calculate customer lifespan in years
        lifespan_days = (last_order - first_order).days
        if lifespan_days == 0:
            return 1.0
        
        lifespan_years = lifespan_days / 365.25
        orders_count = len(order_dates)
        
        return orders_count / lifespan_years
    
    def _calculate_customer_lifespan(self, customer_data: Dict) -> int:
        """Calculate customer lifespan in days"""
        
        if customer_data["platform_created_at"] and customer_data["last_order_date"]:
            lifespan = (customer_data["last_order_date"] - customer_data["platform_created_at"]).days
            return max(lifespan, 1)  # At least 1 day
        
        # Fallback: estimate based on order span
        if len(customer_data["order_dates"]) > 1:
            order_span = (max(customer_data["order_dates"]) - min(customer_data["order_dates"])).days
            return max(order_span, 1)
        
        return 365  # Default to 1 year for new customers
    
    def _calculate_confidence_intervals(self, customer_data: Dict, base_clv: float) -> Tuple[float, float]:
        """Calculate CLV confidence intervals based on order volatility"""
        
        if len(customer_data["order_amounts"]) < 2:
            # High uncertainty for customers with few orders
            return base_clv * 0.5, base_clv * 1.5
        
        amounts = customer_data["order_amounts"]
        volatility = np.std(amounts) / np.mean(amounts) if np.mean(amounts) > 0 else 1.0
        
        # Higher volatility = wider confidence intervals
        uncertainty_factor = min(0.5 + volatility, 2.0)  # Cap at 200% uncertainty
        
        return (
            base_clv * (1 - uncertainty_factor * 0.3),
            base_clv * (1 + uncertainty_factor * 0.3)
        )
    
    def _calculate_churn_risk(self, customer_data: Dict) -> float:
        """Calculate churn risk score (0-1)"""
        
        days_since_last_order = customer_data["days_since_last_order"]
        total_orders = customer_data["total_orders"]
        
        # Base risk on recency
        recency_risk = min(days_since_last_order / 180.0, 1.0)  # 180 days = full risk
        
        # Frequency factor (more orders = lower risk)
        frequency_risk = max(0.8 - (total_orders * 0.05), 0.1)  # Min 10% risk
        
        # Combined risk score
        combined_risk = (recency_risk * 0.7) + (frequency_risk * 0.3)
        
        return min(combined_risk, 1.0)
    
    def _determine_segment(self, clv: float, customer_data: Dict) -> str:
        """Determine customer segment based on CLV and behavior"""
        
        total_orders = customer_data["total_orders"]
        days_since_last_order = customer_data["days_since_last_order"]
        
        if clv >= 5000:
            return "VIP"
        elif clv >= 2000:
            return "High Value"
        elif clv >= 500:
            if days_since_last_order > 90:
                return "At Risk"
            else:
                return "Regular"
        elif total_orders == 1:
            return "New Customer"
        else:
            return "Low Value"
    
    def _get_customer_list(self, platform: Optional[str] = None, limit: int = 1000) -> List[Dict]:
        """Get list of customers for bulk processing"""
        
        query = """
        SELECT external_id, platform 
        FROM universal_customers 
        WHERE orders_count > 0
        """
        
        params = {}
        if platform:
            query += " AND platform = :platform"
            params["platform"] = platform
            
        query += f" ORDER BY total_spent DESC LIMIT {limit}"
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params)
                return [{"external_id": row[0], "platform": row[1]} for row in result.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get customer list: {str(e)}")
            raise