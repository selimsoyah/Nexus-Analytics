"""
Modular ETL Engine

This module provides a flexible ETL system that can ingest data from any 
e-commerce platform and transform it to our universal schema.
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime
import json
import requests

# Import our components
from .platform_configs import get_platform_config, list_supported_platforms
from .data_mapper import DataMapper, MultiPlatformMapper

# Import schemas (adjust path for direct execution)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas.universal import (
    Base, UniversalCustomer, UniversalProduct, UniversalOrder, 
    UniversalOrderItem, UniversalCustomerSegment
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModularETL:
    """
    Universal ETL engine that can process data from any e-commerce platform
    """
    
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.multi_mapper = MultiPlatformMapper()
        
        # Initialize all platform mappers
        for platform_name in list_supported_platforms():
            config = get_platform_config(platform_name)
            self.multi_mapper.add_platform(config)
    
    def create_universal_tables(self):
        """Create universal tables if they don't exist"""
        logger.info("Ensuring universal database tables exist...")
        Base.metadata.create_all(self.engine)
        logger.info("Universal tables ready!")
    
    def ingest_platform_data(self, 
                           platform: str, 
                           data_source: Union[str, Dict, pd.DataFrame], 
                           data_type: str,
                           batch_size: int = 1000) -> Dict[str, Any]:
        """
        Generic ingestion method for any platform
        
        Args:
            platform: Platform name ('shopify', 'woocommerce', 'generic_csv', etc.)
            data_source: File path, API endpoint, DataFrame, or data dict
            data_type: Type of data ('customers', 'orders', 'products', 'order_items')
            batch_size: Number of records to process at once
        
        Returns:
            Dictionary with ingestion results
        """
        logger.info(f"Starting ingestion: {platform} -> {data_type}")
        
        try:
            # Validate platform
            if platform not in list_supported_platforms():
                raise ValueError(f"Unsupported platform: {platform}")
            
            # Load raw data
            raw_data = self._load_data(data_source)
            logger.info(f"Loaded {len(raw_data)} raw records")
            
            # Transform to universal format
            universal_data = self.multi_mapper.transform_data(platform, raw_data, data_type)
            logger.info(f"Transformed to {len(universal_data)} universal records")
            
            # Validate data
            validation = self.multi_mapper.mappers[platform].validate_data(universal_data)
            if not validation['is_valid']:
                logger.error(f"Data validation failed: {validation['errors']}")
                return {
                    'success': False,
                    'error': 'Data validation failed',
                    'validation': validation
                }
            
            if validation['warnings']:
                logger.warning(f"Data warnings: {validation['warnings']}")
            
            # Load to universal tables
            table_name = f"universal_{data_type}"
            records_inserted = self._load_to_database(universal_data, table_name, batch_size)
            
            result = {
                'success': True,
                'platform': platform,
                'data_type': data_type,
                'records_processed': len(raw_data),
                'records_inserted': records_inserted,
                'validation': validation,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Successfully ingested {records_inserted} {data_type} records from {platform}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'platform': platform,
                'data_type': data_type,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _load_data(self, data_source: Union[str, Dict, pd.DataFrame]) -> pd.DataFrame:
        """Flexible data loading from various sources"""
        
        if isinstance(data_source, pd.DataFrame):
            return data_source
        
        elif isinstance(data_source, dict):
            return pd.DataFrame(data_source)
        
        elif isinstance(data_source, str):
            if data_source.startswith('http'):
                # API endpoint
                return self._load_from_api(data_source)
            elif data_source.endswith('.csv'):
                return pd.read_csv(data_source)
            elif data_source.endswith('.json'):
                return pd.read_json(data_source)
            elif data_source.endswith('.xlsx') or data_source.endswith('.xls'):
                return pd.read_excel(data_source)
            else:
                raise ValueError(f"Unsupported file format: {data_source}")
        
        else:
            raise ValueError(f"Unsupported data source type: {type(data_source)}")
    
    def _load_from_api(self, api_url: str) -> pd.DataFrame:
        """Load data from API endpoint"""
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            # Handle different API response formats
            if isinstance(data, list):
                return pd.DataFrame(data)
            elif isinstance(data, dict):
                # Look for common data keys
                for key in ['data', 'results', 'items', 'records']:
                    if key in data and isinstance(data[key], list):
                        return pd.DataFrame(data[key])
                # If no standard key found, treat whole dict as single record
                return pd.DataFrame([data])
            else:
                raise ValueError("API response is not in expected format")
                
        except requests.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def _load_to_database(self, data: pd.DataFrame, table_name: str, batch_size: int) -> int:
        """Load data to database in batches"""
        total_inserted = 0
        
        # Process in batches
        for i in range(0, len(data), batch_size):
            batch = data.iloc[i:i + batch_size]
            
            try:
                # Use pandas to_sql with append mode
                batch.to_sql(table_name, self.engine, if_exists='append', index=False, method='multi')
                total_inserted += len(batch)
                
                if len(data) > batch_size:
                    logger.info(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
                    
            except Exception as e:
                logger.error(f"Failed to insert batch {i//batch_size + 1}: {str(e)}")
                # Continue with next batch instead of failing completely
                continue
        
        return total_inserted
    
    def preview_ingestion(self, platform: str, data_source: Union[str, Dict, pd.DataFrame], 
                         data_type: str, sample_size: int = 5) -> Dict[str, Any]:
        """
        Preview what the ingestion would look like without actually inserting data
        """
        try:
            # Load sample data
            raw_data = self._load_data(data_source)
            sample_data = raw_data.head(sample_size)
            
            # Get preview from mapper
            mapper = self.multi_mapper.mappers[platform]
            preview = mapper.preview_transformation(sample_data)
            
            return {
                'success': True,
                'preview': preview,
                'total_records_available': len(raw_data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested data"""
        with self.engine.connect() as conn:
            stats = {}
            
            # Count records by platform in each table
            tables = ['universal_customers', 'universal_products', 'universal_orders', 'universal_order_items']
            
            for table in tables:
                try:
                    result = conn.execute(text(f"""
                        SELECT platform, COUNT(*) as count 
                        FROM {table} 
                        GROUP BY platform
                    """))
                    
                    stats[table] = {row[0]: row[1] for row in result}
                    
                except Exception as e:
                    stats[table] = {'error': str(e)}
            
            return stats
    
    def cross_platform_analytics(self) -> Dict[str, Any]:
        """Generate analytics that work across all platforms"""
        with self.engine.connect() as conn:
            analytics = {}
            
            try:
                # Total customers by platform
                result = conn.execute(text("""
                    SELECT platform, COUNT(*) as customers, SUM(total_spent) as revenue
                    FROM universal_customers 
                    GROUP BY platform
                """))
                analytics['customers_by_platform'] = {row[0]: {'count': row[1], 'revenue': float(row[2] or 0)} for row in result}
                
                # Top products across all platforms
                result = conn.execute(text("""
                    SELECT p.name, p.platform, SUM(oi.quantity) as units_sold, SUM(oi.total_price) as revenue
                    FROM universal_products p
                    JOIN universal_order_items oi ON p.id = oi.product_id
                    GROUP BY p.name, p.platform
                    ORDER BY revenue DESC
                    LIMIT 10
                """))
                analytics['top_products'] = [
                    {'name': row[0], 'platform': row[1], 'units_sold': row[2], 'revenue': float(row[3])}
                    for row in result
                ]
                
                # Monthly sales trends
                result = conn.execute(text("""
                    SELECT DATE_TRUNC('month', order_date) as month, 
                           platform, 
                           COUNT(*) as orders, 
                           SUM(total_amount) as revenue
                    FROM universal_orders 
                    WHERE order_date >= NOW() - INTERVAL '12 months'
                    GROUP BY month, platform
                    ORDER BY month DESC
                """))
                analytics['monthly_trends'] = [
                    {'month': row[0].isoformat(), 'platform': row[1], 'orders': row[2], 'revenue': float(row[3])}
                    for row in result
                ]
                
            except Exception as e:
                analytics['error'] = str(e)
            
            return analytics
    
    def sync_platform_data(self, platform: str, incremental: bool = True) -> Dict[str, Any]:
        """
        Sync data from a platform (useful for regular updates)
        
        Args:
            platform: Platform to sync
            incremental: If True, only sync new/updated records
        """
        # This would be implemented based on each platform's API capabilities
        # For now, return a placeholder
        return {
            'success': False,
            'message': f'Incremental sync not yet implemented for {platform}',
            'timestamp': datetime.utcnow().isoformat()
        }


# Convenience functions for common operations
def quick_csv_ingestion(csv_file_path: str, platform: str, data_type: str, db_url: str) -> Dict[str, Any]:
    """Quick function to ingest CSV data"""
    etl = ModularETL(db_url)
    etl.create_universal_tables()
    return etl.ingest_platform_data(platform, csv_file_path, data_type)


def preview_csv_transformation(csv_file_path: str, platform: str, data_type: str) -> Dict[str, Any]:
    """Preview how CSV data would be transformed"""
    etl = ModularETL("sqlite:///:memory:")  # Use in-memory DB for preview
    return etl.preview_ingestion(platform, csv_file_path, data_type)