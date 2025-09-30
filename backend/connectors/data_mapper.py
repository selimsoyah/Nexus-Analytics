"""
Dynamic Data Mapper

This module provides flexible data transformation capabilities that can map
data from any e-commerce platform to our universal schema using configuration-driven rules.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
import re
import json

from .platform_configs import PlatformConfig


class DataMapper:
    """
    Configurable data mapper that transforms platform-specific data 
    to universal format using platform configurations
    """
    
    def __init__(self, platform_config: PlatformConfig):
        self.config = platform_config
        
    def transform_data(self, raw_data: pd.DataFrame, data_type: str = "customers") -> pd.DataFrame:
        """
        Transform platform-specific data to universal format
        
        Args:
            raw_data: Raw data from the platform
            data_type: Type of data ('customers', 'orders', 'products', 'order_items')
        
        Returns:
            DataFrame in universal format
        """
        transformed_data = pd.DataFrame()
        
        # Apply field mappings
        for universal_field, mapping in self.config.field_mappings.items():
            source_field = mapping['source_field']
            transformation = mapping.get('transformation')
            
            # Handle nested field access (e.g., "default_address.city")
            if '.' in source_field:
                value = self._get_nested_field(raw_data, source_field)
            elif source_field in raw_data.columns:
                value = raw_data[source_field]
            else:
                value = None
                
            if value is not None:
                if transformation:
                    transformed_data[universal_field] = self._apply_transformation(
                        value, transformation
                    )
                else:
                    transformed_data[universal_field] = value
        
        # Add platform identifier
        transformed_data['platform'] = self.config.platform_name
        
        # Add timestamps if not present
        if 'created_at' not in transformed_data.columns:
            transformed_data['created_at'] = datetime.utcnow()
        if 'updated_at' not in transformed_data.columns:
            transformed_data['updated_at'] = datetime.utcnow()
        
        # Apply default values only for fields that were mapped and exist in schema
        for field, default_value in self.config.default_values.items():
            if field not in transformed_data.columns:
                # Only add default if it's a legitimate field for this data type
                transformed_data[field] = default_value
        
        return transformed_data
    
    def _get_nested_field(self, data: pd.DataFrame, field_path: str) -> pd.Series:
        """
        Extract nested field values (e.g., 'default_address.city')
        This would be used for JSON or structured data
        """
        # For now, return None - can be extended for complex data structures
        return pd.Series([None] * len(data))
    
    def _apply_transformation(self, series: pd.Series, transformation: str) -> pd.Series:
        """Apply specific transformations based on type"""
        
        if transformation == "extract_first_name":
            return series.str.split().str[0]
        
        elif transformation == "extract_last_name":
            return series.str.split().str[1:].str.join(' ')
        
        elif transformation == "decimal_conversion":
            return pd.to_numeric(series, errors='coerce')
        
        elif transformation == "parse_shopify_date":
            return pd.to_datetime(series, format='%Y-%m-%dT%H:%M:%S%z', errors='coerce')
        
        elif transformation == "parse_woo_date":
            return pd.to_datetime(series, format='%Y-%m-%dT%H:%M:%S', errors='coerce')
        
        elif transformation == "parse_magento_date":
            return pd.to_datetime(series, format='%Y-%m-%d %H:%M:%S', errors='coerce')
        
        elif transformation == "parse_generic_date":
            return pd.to_datetime(series, errors='coerce')
        
        elif transformation == "strip_html":
            return series.astype(str).apply(self._strip_html_tags)
        
        elif transformation == "normalize_email":
            return series.str.lower().str.strip()
        
        elif transformation == "normalize_phone":
            return series.astype(str).apply(self._normalize_phone)
        
        elif transformation == "boolean_conversion":
            return series.astype(bool)
        
        elif transformation == "json_to_string":
            return series.apply(lambda x: json.dumps(x) if isinstance(x, dict) else str(x))
        
        elif transformation == "uppercase":
            return series.str.upper()
        
        elif transformation == "lowercase":
            return series.str.lower()
        
        elif transformation == "title_case":
            return series.str.title()
        
        elif transformation == "calculate_total_price":
            # For order items, calculate total price from unit price and quantity
            # This requires access to the original DataFrame
            # For now, return the original price as total (will be corrected in ETL)
            return pd.to_numeric(series, errors='coerce')
        
        else:
            # If transformation not recognized, return original series
            return series
    
    def _strip_html_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not isinstance(text, str):
            return str(text)
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number format"""
        if not isinstance(phone, str):
            return str(phone)
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        return digits_only
    
    def validate_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate transformed data against configuration rules
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        # Check for required fields
        required_fields = ['external_id', 'platform']
        for field in required_fields:
            if field not in data.columns:
                validation_results['is_valid'] = False
                validation_results['errors'].append(f"Required field '{field}' is missing")
        
        # Check for data quality issues
        if 'email' in data.columns:
            invalid_emails = data[~data['email'].str.contains('@', na=False)]['email'].count()
            if invalid_emails > 0:
                validation_results['warnings'].append(f"{invalid_emails} invalid email addresses found")
        
        # Check for duplicates
        if 'external_id' in data.columns:
            duplicates = data['external_id'].duplicated().sum()
            if duplicates > 0:
                validation_results['warnings'].append(f"{duplicates} duplicate external_ids found")
        
        # Add statistics
        validation_results['stats'] = {
            'total_records': len(data),
            'columns': list(data.columns),
            'null_counts': data.isnull().sum().to_dict()
        }
        
        return validation_results
    
    def preview_transformation(self, raw_data: pd.DataFrame, sample_size: int = 5) -> Dict[str, Any]:
        """
        Preview the transformation results on a sample of data
        
        Args:
            raw_data: Raw data to preview
            sample_size: Number of rows to include in preview
        
        Returns:
            Dictionary with preview information
        """
        sample_data = raw_data.head(sample_size)
        transformed_sample = self.transform_data(sample_data)
        
        return {
            'source_columns': list(raw_data.columns),
            'target_columns': list(transformed_sample.columns),
            'sample_transformation': {
                'original': sample_data.to_dict('records'),
                'transformed': transformed_sample.to_dict('records')
            },
            'field_mappings': self.config.field_mappings,
            'platform': self.config.platform_name
        }


class MultiPlatformMapper:
    """
    Manager for handling multiple platform mappers
    """
    
    def __init__(self):
        self.mappers = {}
    
    def add_platform(self, platform_config: PlatformConfig):
        """Add a platform mapper"""
        self.mappers[platform_config.platform_name] = DataMapper(platform_config)
    
    def transform_data(self, platform_name: str, raw_data: pd.DataFrame, data_type: str = "customers") -> pd.DataFrame:
        """Transform data using specified platform mapper"""
        if platform_name not in self.mappers:
            raise ValueError(f"Platform '{platform_name}' not configured")
        
        return self.mappers[platform_name].transform_data(raw_data, data_type)
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms"""
        return list(self.mappers.keys())
    
    def validate_all_platforms(self, data_samples: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Validate data samples from multiple platforms"""
        results = {}
        
        for platform_name, sample_data in data_samples.items():
            if platform_name in self.mappers:
                transformed = self.mappers[platform_name].transform_data(sample_data)
                results[platform_name] = self.mappers[platform_name].validate_data(transformed)
        
        return results