"""
Customer Segmentation System

This module provides comprehensive customer segmentation capabilities using:
1. RFM Analysis (Recency, Frequency, Monetary)
2. Rule-based customer classification
3. K-means clustering for behavioral segmentation
4. Predictive segment assignment for new customers

Business Value:
- Identify VIP customers for premium treatment
- Target at-risk customers for retention campaigns
- Optimize marketing spend by customer segment
- Personalize customer experience based on behavior patterns
"""

from sqlalchemy import create_engine, text
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CustomerSegmentProfile:
    """Data class for customer segment profile"""
    customer_id: str
    platform: str
    
    # RFM Scores
    recency_score: int          # 1-5 (5 = most recent purchase)
    frequency_score: int        # 1-5 (5 = most frequent buyer)
    monetary_score: int         # 1-5 (5 = highest spender)
    rfm_score: str             # Combined RFM score (e.g., "555")
    
    # RFM Raw Values
    recency_days: int          # Days since last purchase
    frequency_count: int       # Total number of orders
    monetary_value: float      # Total amount spent
    
    # Segment Classifications
    rfm_segment: str           # RFM-based segment name
    ml_segment: str            # ML clustering segment
    business_segment: str      # Final business segment
    
    # Additional Metrics
    avg_order_value: float
    customer_lifespan_days: int
    churn_risk_score: float
    segment_confidence: float   # Confidence in segment assignment
    
    # Recommendations
    recommended_actions: List[str]
    segment_priority: int      # 1-5 (5 = highest priority)

class CustomerSegmentationEngine:
    """
    Advanced customer segmentation using RFM analysis and machine learning
    """
    
    def __init__(self, db_url: str = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"):
        self.engine = create_engine(db_url)
        self.scaler = StandardScaler()
        self.kmeans_model = None
        
        # RFM Segment Definitions
        self.rfm_segments = {
            # Champions (555, 554, 544, 545, 454, 455, 445)
            'Champions': {
                'description': 'Best customers who bought recently, buy often and spend the most',
                'priority': 5,
                'actions': [
                    'Reward them for loyalty',
                    'Ask for reviews and referrals', 
                    'Offer new products first',
                    'Provide VIP customer service'
                ]
            },
            
            # Loyal Customers (543, 444, 435, 355, 354, 345, 344, 335)
            'Loyal Customers': {
                'description': 'Spend good money and buy often but not recently',
                'priority': 4,
                'actions': [
                    'Recommend other products',
                    'Send personalized offers',
                    'Maintain regular engagement',
                    'Thank them for loyalty'
                ]
            },
            
            # Potential Loyalists (512, 511, 422, 421, 412, 411, 311)
            'Potential Loyalists': {
                'description': 'Recent customers with average frequency and spending',
                'priority': 3,
                'actions': [
                    'Offer membership or loyalty program',
                    'Recommend popular products',
                    'Send educational content',
                    'Create targeted campaigns'
                ]
            },
            
            # New Customers (512, 511, 512, 411, 311)
            'New Customers': {
                'description': 'Recently acquired customers with low frequency',
                'priority': 3,
                'actions': [
                    'Provide onboarding support',
                    'Send welcome series',
                    'Offer first-time buyer incentives',
                    'Focus on customer education'
                ]
            },
            
            # Promising (414, 415, 315, 314, 313)
            'Promising': {
                'description': 'Recent shoppers but spent and bought few times',
                'priority': 2,
                'actions': [
                    'Create awareness campaigns',
                    'Offer free shipping',
                    'Provide product recommendations',
                    'Send engaging content'
                ]
            },
            
            # Need Attention (155, 154, 144, 214, 215, 115, 114)
            'Need Attention': {
                'description': 'Above average recency, frequency and monetary values',
                'priority': 4,
                'actions': [
                    'Make limited time offers',
                    'Recommend based on past purchases',
                    'Reactivate with special deals',
                    'Send personalized messages'
                ]
            },
            
            # About to Sleep (244, 235, 234, 245, 235, 234)
            'About to Sleep': {
                'description': 'Below average recency and frequency',
                'priority': 3,
                'actions': [
                    'Share valuable resources',
                    'Recommend popular products',
                    'Win back campaign with discount',
                    'Send engaging content'
                ]
            },
            
            # At Risk (155, 154, 144, 214, 215, 115, 114)
            'At Risk': {
                'description': 'Some time since they purchased, low spenders, low frequency',
                'priority': 4,
                'actions': [
                    'Send personalized reactivation emails',
                    'Offer renewal discount',
                    'Share helpful resources',
                    'Provide excellent customer service'
                ]
            },
            
            # Cannot Lose Them (145, 155, 154, 144, 214, 215, 115, 114)
            'Cannot Lose Them': {
                'description': 'Made big purchases and often but long time ago',
                'priority': 5,
                'actions': [
                    'Win them back with renewals or newer products',
                    'Provide exclusive offers',
                    'Reach out personally',
                    'Offer VIP customer service'
                ]
            },
            
            # Hibernating (332, 231, 241, 221, 213, 131, 141, 121)
            'Hibernating': {
                'description': 'Last purchase was long back, low spenders and low frequency',
                'priority': 1,
                'actions': [
                    'Create awareness with blog articles',
                    'Ignore unless they re-engage',
                    'Very low-cost reactivation attempts',
                    'Remove from expensive campaigns'
                ]
            },
            
            # Lost (111, 112, 121, 131, 141, 151)
            'Lost': {
                'description': 'Lowest recency, frequency and monetary scores',
                'priority': 1,
                'actions': [
                    'Remove from email lists',
                    'Ignore unless they contact you',
                    'No marketing spend',
                    'Archive customer data'
                ]
            }
        }
    
    def calculate_rfm_scores(self, platform: Optional[str] = None) -> pd.DataFrame:
        """
        Calculate RFM scores for all customers
        
        Args:
            platform: Filter by platform (optional)
            
        Returns:
            DataFrame with RFM scores and raw values
        """
        
        # Get customer data with order aggregations
        query = """
        SELECT 
            c.external_id as customer_id,
            c.platform,
            c.email,
            c.first_name,
            c.last_name,
            
            -- Recency: Days since last order
            CASE 
                WHEN c.last_order_date IS NOT NULL 
                THEN (CURRENT_DATE - c.last_order_date::date)
                ELSE 9999
            END as recency_days,
            
            -- Frequency: Total number of orders
            COALESCE(c.orders_count, 0) as frequency_count,
            
            -- Monetary: Total amount spent
            COALESCE(c.total_spent, 0) as monetary_value,
            
            -- Additional metrics
            COALESCE(c.average_order_value, 0) as avg_order_value,
            
            -- Customer lifespan in days
            CASE 
                WHEN c.platform_created_at IS NOT NULL AND c.last_order_date IS NOT NULL
                THEN (c.last_order_date::date - c.platform_created_at::date)
                ELSE 0
            END as customer_lifespan_days,
            
            c.last_order_date,
            c.platform_created_at
            
        FROM universal_customers c
        WHERE c.orders_count > 0
        """
        
        params = {}
        if platform:
            query += " AND c.platform = :platform"
            params["platform"] = platform
            
        query += " ORDER BY monetary_value DESC"
        
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params)
                
                if df.empty:
                    logger.warning("No customer data found for RFM analysis")
                    return pd.DataFrame()
                
                # Calculate RFM scores using quintiles (1-5 scale)
                df['recency_score'] = pd.qcut(df['recency_days'].rank(method='first'), 
                                            q=5, labels=[5,4,3,2,1]).astype(int)
                
                df['frequency_score'] = pd.qcut(df['frequency_count'].rank(method='first'), 
                                              q=5, labels=[1,2,3,4,5]).astype(int)
                
                df['monetary_score'] = pd.qcut(df['monetary_value'].rank(method='first'), 
                                             q=5, labels=[1,2,3,4,5]).astype(int)
                
                # Create combined RFM score
                df['rfm_score'] = (df['recency_score'].astype(str) + 
                                 df['frequency_score'].astype(str) + 
                                 df['monetary_score'].astype(str))
                
                # Assign RFM segments
                df['rfm_segment'] = df['rfm_score'].apply(self._assign_rfm_segment)
                
                # Calculate churn risk score
                df['churn_risk_score'] = self._calculate_churn_risk(df)
                
                logger.info(f"Successfully calculated RFM scores for {len(df)} customers")
                return df
                
        except Exception as e:
            logger.error(f"RFM calculation failed: {str(e)}")
            raise
    
    def _assign_rfm_segment(self, rfm_score: str) -> str:
        """
        Assign RFM segment based on RFM score
        
        Args:
            rfm_score: Three-digit RFM score (e.g., "555")
            
        Returns:
            Segment name
        """
        
        # Convert string to individual scores
        try:
            r, f, m = int(rfm_score[0]), int(rfm_score[1]), int(rfm_score[2])
        except:
            return 'Unknown'
        
        # Champions: High value across all dimensions
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        
        # Loyal Customers: High frequency and monetary, moderate recency
        elif f >= 3 and m >= 3 and r >= 2:
            return 'Loyal Customers'
        
        # Cannot Lose Them: High monetary, low recency
        elif m >= 4 and r <= 2:
            return 'Cannot Lose Them'
        
        # At Risk: Moderate monetary, low recency and frequency
        elif m >= 2 and r <= 2 and f <= 2:
            return 'At Risk'
        
        # New Customers: High recency, low frequency
        elif r >= 4 and f <= 2:
            return 'New Customers'
        
        # Potential Loyalists: Good recency, moderate frequency and monetary
        elif r >= 3 and f >= 2 and m >= 2:
            return 'Potential Loyalists'
        
        # Need Attention: Moderate across all dimensions
        elif r >= 2 and f >= 2 and m >= 2:
            return 'Need Attention'
        
        # Promising: High recency, low frequency and monetary
        elif r >= 3 and f <= 2 and m <= 2:
            return 'Promising'
        
        # About to Sleep: Low recency, moderate frequency and monetary
        elif r <= 2 and f >= 2 and m >= 2:
            return 'About to Sleep'
        
        # Hibernating: Low recency and frequency, some monetary value
        elif r <= 2 and f <= 2 and m >= 1:
            return 'Hibernating'
        
        # Lost: Low across all dimensions
        else:
            return 'Lost'
    
    def _calculate_churn_risk(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate churn risk score based on RFM values
        
        Args:
            df: DataFrame with RFM scores
            
        Returns:
            Series with churn risk scores (0-1)
        """
        
        # Normalize recency (higher days = higher risk)
        recency_risk = df['recency_days'] / df['recency_days'].max()
        
        # Normalize frequency (lower frequency = higher risk)
        frequency_risk = 1 - (df['frequency_count'] / df['frequency_count'].max())
        
        # Normalize monetary (lower spend = higher risk)
        monetary_risk = 1 - (df['monetary_value'] / df['monetary_value'].max())
        
        # Combined risk score (weighted average)
        churn_risk = (recency_risk * 0.5 + frequency_risk * 0.3 + monetary_risk * 0.2)
        
        return churn_risk.clip(0, 1)
    
    def perform_kmeans_clustering(self, df: pd.DataFrame, n_clusters: int = 5) -> pd.DataFrame:
        """
        Perform K-means clustering on customer data
        
        Args:
            df: DataFrame with RFM data
            n_clusters: Number of clusters to create
            
        Returns:
            DataFrame with ML segment assignments
        """
        
        if df.empty:
            return df
        
        try:
            # Select features for clustering
            features = ['recency_days', 'frequency_count', 'monetary_value', 'customer_lifespan_days']
            X = df[features].fillna(0)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Optimal number of clusters using elbow method
            if n_clusters == 'auto':
                n_clusters = self._find_optimal_clusters(X_scaled)
            
            # Ensure we don't have more clusters than samples
            n_clusters = min(n_clusters, len(df))
            
            if n_clusters < 2:
                # Not enough data for clustering
                df['ml_cluster'] = 0
                df['ml_segment'] = 'Single_Group'
                logger.info(f"Insufficient data for clustering (n={len(df)}). Assigning single group.")
                return df
            
            # Perform clustering
            self.kmeans_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = self.kmeans_model.fit_predict(X_scaled)
            
            # Add cluster labels to dataframe
            df['ml_cluster'] = cluster_labels
            df['ml_segment'] = df['ml_cluster'].apply(lambda x: f'ML_Cluster_{x}')
            
            # Calculate silhouette score for clustering quality
            if len(df) > n_clusters:
                silhouette_avg = silhouette_score(X_scaled, cluster_labels)
                logger.info(f"K-means clustering completed. Silhouette score: {silhouette_avg:.3f}")
            
            # Analyze clusters and assign meaningful names
            df = self._assign_meaningful_cluster_names(df)
            
            return df
            
        except Exception as e:
            logger.error(f"K-means clustering failed: {str(e)}")
            df['ml_segment'] = 'Unknown'
            return df
    
    def _find_optimal_clusters(self, X: np.ndarray, max_clusters: int = 8) -> int:
        """
        Find optimal number of clusters using elbow method
        
        Args:
            X: Scaled feature matrix
            max_clusters: Maximum number of clusters to test
            
        Returns:
            Optimal number of clusters
        """
        
        inertias = []
        cluster_range = range(2, min(max_clusters + 1, len(X)))
        
        for n in cluster_range:
            kmeans = KMeans(n_clusters=n, random_state=42, n_init=10)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)
        
        # Simple elbow detection (find the point where improvement slows down)
        if len(inertias) < 2:
            return 3
        
        # Calculate rate of change
        rates = []
        for i in range(1, len(inertias)):
            rate = (inertias[i-1] - inertias[i]) / inertias[i-1]
            rates.append(rate)
        
        # Find elbow point (where rate of improvement drops significantly)
        for i in range(1, len(rates)):
            if rates[i] < rates[i-1] * 0.5:  # 50% drop in improvement rate
                return list(cluster_range)[i]
        
        # Default to middle value if no clear elbow
        return max(3, len(cluster_range) // 2)
    
    def _assign_meaningful_cluster_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assign meaningful names to ML clusters based on their characteristics
        
        Args:
            df: DataFrame with cluster assignments
            
        Returns:
            DataFrame with meaningful cluster names
        """
        
        cluster_profiles = {}
        
        for cluster in df['ml_cluster'].unique():
            cluster_data = df[df['ml_cluster'] == cluster]
            
            profile = {
                'avg_recency': cluster_data['recency_days'].mean(),
                'avg_frequency': cluster_data['frequency_count'].mean(),
                'avg_monetary': cluster_data['monetary_value'].mean(),
                'size': len(cluster_data)
            }
            
            cluster_profiles[cluster] = profile
        
        # Assign names based on cluster characteristics
        cluster_names = {}
        for cluster, profile in cluster_profiles.items():
            if profile['avg_monetary'] > df['monetary_value'].quantile(0.8):
                if profile['avg_frequency'] > df['frequency_count'].quantile(0.6):
                    cluster_names[cluster] = 'ML_VIP_Frequent'
                else:
                    cluster_names[cluster] = 'ML_High_Value'
            elif profile['avg_frequency'] > df['frequency_count'].quantile(0.7):
                cluster_names[cluster] = 'ML_Frequent_Buyers'
            elif profile['avg_recency'] < df['recency_days'].quantile(0.3):
                cluster_names[cluster] = 'ML_Recent_Active'
            elif profile['avg_recency'] > df['recency_days'].quantile(0.7):
                cluster_names[cluster] = 'ML_Dormant_Risk'
            else:
                cluster_names[cluster] = f'ML_Regular_{cluster}'
        
        # Apply meaningful names
        df['ml_segment'] = df['ml_cluster'].map(cluster_names)
        
        return df
    
    def create_customer_profiles(self, platform: Optional[str] = None) -> List[CustomerSegmentProfile]:
        """
        Create comprehensive customer segment profiles
        
        Args:
            platform: Filter by platform (optional)
            
        Returns:
            List of CustomerSegmentProfile objects
        """
        
        # Calculate RFM scores
        rfm_df = self.calculate_rfm_scores(platform)
        
        if rfm_df.empty:
            return []
        
        # Perform ML clustering
        rfm_df = self.perform_kmeans_clustering(rfm_df)
        
        # Create customer profiles
        profiles = []
        
        for _, customer in rfm_df.iterrows():
            # Determine final business segment (prioritize RFM over ML)
            business_segment = customer['rfm_segment']
            
            # Get segment info
            segment_info = self.rfm_segments.get(business_segment, {})
            
            profile = CustomerSegmentProfile(
                customer_id=customer['customer_id'],
                platform=customer['platform'],
                
                # RFM Scores
                recency_score=customer['recency_score'],
                frequency_score=customer['frequency_score'],
                monetary_score=customer['monetary_score'],
                rfm_score=customer['rfm_score'],
                
                # RFM Raw Values
                recency_days=customer['recency_days'],
                frequency_count=customer['frequency_count'],
                monetary_value=customer['monetary_value'],
                
                # Segment Classifications
                rfm_segment=customer['rfm_segment'],
                ml_segment=customer.get('ml_segment', 'Unknown'),
                business_segment=business_segment,
                
                # Additional Metrics
                avg_order_value=customer['avg_order_value'],
                customer_lifespan_days=customer['customer_lifespan_days'],
                churn_risk_score=customer['churn_risk_score'],
                segment_confidence=self._calculate_segment_confidence(customer),
                
                # Recommendations
                recommended_actions=segment_info.get('actions', []),
                segment_priority=segment_info.get('priority', 1)
            )
            
            profiles.append(profile)
        
        logger.info(f"Created {len(profiles)} customer segment profiles")
        return profiles
    
    def _calculate_segment_confidence(self, customer_data: pd.Series) -> float:
        """
        Calculate confidence in segment assignment
        
        Args:
            customer_data: Customer data series
            
        Returns:
            Confidence score (0-1)
        """
        
        # Base confidence on data completeness and score consistency
        r, f, m = customer_data['recency_score'], customer_data['frequency_score'], customer_data['monetary_score']
        
        # Higher confidence for extreme scores
        score_variance = np.var([r, f, m])
        
        # Lower variance = more consistent scores = higher confidence
        confidence = 1.0 - (score_variance / 4.0)  # Normalize by max possible variance
        
        # Adjust based on data quality
        if customer_data['customer_lifespan_days'] > 30:  # More data = higher confidence
            confidence *= 1.1
        
        if customer_data['frequency_count'] >= 3:  # Multiple orders = higher confidence
            confidence *= 1.1
        
        return min(confidence, 1.0)
    
    def get_segment_summary(self, profiles: List[CustomerSegmentProfile]) -> Dict:
        """
        Get summary statistics for customer segments
        
        Args:
            profiles: List of customer profiles
            
        Returns:
            Dictionary with segment summary statistics
        """
        
        if not profiles:
            return {"error": "No customer profiles available"}
        
        # Convert to DataFrame for easier analysis
        data = []
        for profile in profiles:
            data.append({
                'segment': profile.business_segment,
                'rfm_segment': profile.rfm_segment,
                'ml_segment': profile.ml_segment,
                'platform': profile.platform,
                'monetary_value': profile.monetary_value,
                'frequency_count': profile.frequency_count,
                'recency_days': profile.recency_days,
                'churn_risk_score': profile.churn_risk_score,
                'segment_priority': profile.segment_priority
            })
        
        df = pd.DataFrame(data)
        
        # Segment distribution
        segment_dist = df['segment'].value_counts().to_dict()
        
        # Segment metrics - flatten the multi-level aggregation
        segment_metrics = {}
        for segment in df['segment'].unique():
            segment_data = df[df['segment'] == segment]
            segment_metrics[segment] = {
                'customer_count': len(segment_data),
                'avg_monetary_value': float(segment_data['monetary_value'].mean()),
                'total_monetary_value': float(segment_data['monetary_value'].sum()),
                'avg_frequency': float(segment_data['frequency_count'].mean()),
                'avg_recency_days': float(segment_data['recency_days'].mean()),
                'avg_churn_risk': float(segment_data['churn_risk_score'].mean()),
                'avg_segment_priority': float(segment_data['segment_priority'].mean())
            }
        
        # Platform distribution - simplified
        platform_dist = {}
        for platform in df['platform'].unique():
            platform_dist[platform] = df[df['platform'] == platform]['segment'].value_counts().to_dict()
        
        return {
            'total_customers': len(profiles),
            'segment_distribution': segment_dist,
            'segment_metrics': segment_metrics,
            'platform_distribution': platform_dist,
            'top_segments_by_value': df.groupby('segment')['monetary_value'].sum().sort_values(ascending=False).head(5).to_dict(),
            'high_risk_segments': df[df['churn_risk_score'] > 0.7]['segment'].value_counts().to_dict(),
            'summary_insights': self._generate_segment_insights(df)
        }
    
    def _generate_segment_insights(self, df: pd.DataFrame) -> List[str]:
        """
        Generate business insights from segment analysis
        
        Args:
            df: DataFrame with customer segment data
            
        Returns:
            List of actionable insights
        """
        
        insights = []
        
        # Total revenue by segment
        revenue_by_segment = df.groupby('segment')['monetary_value'].sum().sort_values(ascending=False)
        
        if len(revenue_by_segment) > 0:
            top_segment = revenue_by_segment.index[0]
            top_revenue = revenue_by_segment.iloc[0]
            insights.append(f"'{top_segment}' segment generates ${top_revenue:.2f} total revenue")
        
        # High-risk customers
        high_risk = df[df['churn_risk_score'] > 0.7]
        if len(high_risk) > 0:
            insights.append(f"{len(high_risk)} customers ({len(high_risk)/len(df)*100:.1f}%) are at high churn risk")
        
        # Champions analysis
        champions = df[df['segment'] == 'Champions']
        if len(champions) > 0:
            insights.append(f"{len(champions)} Champions generate ${champions['monetary_value'].sum():.2f} in revenue")
        
        # New customers
        new_customers = df[df['segment'] == 'New Customers']
        if len(new_customers) > 0:
            insights.append(f"{len(new_customers)} New Customers have potential for growth")
        
        # Platform insights
        if 'platform' in df.columns:
            platform_performance = df.groupby('platform')['monetary_value'].mean().sort_values(ascending=False)
            if len(platform_performance) > 1:
                best_platform = platform_performance.index[0]
                insights.append(f"'{best_platform}' platform has highest average customer value")
        
        return insights[:5]  # Return top 5 insights