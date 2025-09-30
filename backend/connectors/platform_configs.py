"""
Platform Configuration System

This module defines configuration classes for different e-commerce platforms,
enabling flexible data mapping and transformation from any platform to our
universal schema.
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import json


class PlatformConfig:
    """
    Configuration class for e-commerce platform data mapping
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.field_mappings = {}
        self.transformations = {}
        self.default_values = {}
        self.validation_rules = {}
        
    def add_field_mapping(self, universal_field: str, platform_field: str, 
                         transformation: Optional[str] = None):
        """Add a field mapping from platform-specific field to universal field"""
        self.field_mappings[universal_field] = {
            'source_field': platform_field,
            'transformation': transformation
        }
        
    def add_default_value(self, field: str, value: Any):
        """Add a default value for a field when it's missing from source data"""
        self.default_values[field] = value
        
    def add_validation_rule(self, field: str, rule: str):
        """Add validation rule for a field"""
        self.validation_rules[field] = rule
        
    def get_config_dict(self) -> Dict:
        """Return configuration as dictionary for serialization"""
        return {
            'platform_name': self.platform_name,
            'field_mappings': self.field_mappings,
            'default_values': self.default_values,
            'validation_rules': self.validation_rules
        }


# Generic CSV Configuration (Your current format)
def create_generic_csv_config() -> PlatformConfig:
    """Configuration for generic CSV format (current system)"""
    config = PlatformConfig("generic_csv")
    
    # Customer mappings (for customers.csv)
    config.add_field_mapping("external_id", "customer_id")
    config.add_field_mapping("email", "email")
    config.add_field_mapping("full_name", "customer_name")
    config.add_field_mapping("first_name", "customer_name", "extract_first_name")
    config.add_field_mapping("last_name", "customer_name", "extract_last_name")
    
    # Order mappings (for orders.csv)
    config.add_field_mapping("order_date", "order_date", "parse_generic_date")
    config.add_field_mapping("total_amount", "total", "decimal_conversion")
    
    # Order item mappings (for order_items.csv)
    config.add_field_mapping("external_id", "order_item_id")  # This was missing!
    config.add_field_mapping("product_name", "product")
    config.add_field_mapping("product_external_id", "product")
    config.add_field_mapping("order_external_id", "order_id")
    config.add_field_mapping("quantity", "quantity")
    config.add_field_mapping("unit_price", "price", "decimal_conversion")
    config.add_field_mapping("total_price", "price", "calculate_total_price")
    
    # Note: Don't add fields that don't exist in universal schema
    # Only add default values for fields that exist in the schema
    return config


# Shopify Configuration
def create_shopify_config() -> PlatformConfig:
    """Configuration for Shopify API/CSV format"""
    config = PlatformConfig("shopify")
    
    # Customer mappings
    config.add_field_mapping("external_id", "id")
    config.add_field_mapping("email", "email")
    config.add_field_mapping("first_name", "first_name")
    config.add_field_mapping("last_name", "last_name")
    config.add_field_mapping("phone", "phone")
    config.add_field_mapping("platform_created_at", "created_at", "parse_shopify_date")
    config.add_field_mapping("total_spent", "total_spent", "decimal_conversion")
    config.add_field_mapping("orders_count", "orders_count")
    config.add_field_mapping("address_line_1", "default_address.address1")
    config.add_field_mapping("city", "default_address.city")
    config.add_field_mapping("country", "default_address.country")
    config.add_field_mapping("postal_code", "default_address.zip")
    
    # Order mappings
    config.add_field_mapping("order_number", "order_number")
    config.add_field_mapping("order_date", "created_at", "parse_shopify_date")
    config.add_field_mapping("subtotal", "subtotal_price", "decimal_conversion")
    config.add_field_mapping("tax_amount", "total_tax", "decimal_conversion")
    config.add_field_mapping("shipping_amount", "total_shipping", "decimal_conversion")
    config.add_field_mapping("total_amount", "total_price", "decimal_conversion")
    config.add_field_mapping("status", "financial_status")
    config.add_field_mapping("fulfillment_status", "fulfillment_status")
    
    # Product mappings
    config.add_field_mapping("name", "title")
    config.add_field_mapping("description", "body_html", "strip_html")
    config.add_field_mapping("sku", "variants.0.sku")
    config.add_field_mapping("price", "variants.0.price", "decimal_conversion")
    config.add_field_mapping("inventory_quantity", "variants.0.inventory_quantity")
    config.add_field_mapping("vendor", "vendor")
    config.add_field_mapping("product_type", "product_type")
    config.add_field_mapping("tags", "tags")
    
    # Default values
    config.add_default_value("platform", "shopify")
    config.add_default_value("currency", "USD")
    
    return config


# WooCommerce Configuration
def create_woocommerce_config() -> PlatformConfig:
    """Configuration for WooCommerce API/export format"""
    config = PlatformConfig("woocommerce")
    
    # Customer mappings
    config.add_field_mapping("external_id", "id")
    config.add_field_mapping("email", "email")
    config.add_field_mapping("first_name", "first_name")
    config.add_field_mapping("last_name", "last_name")
    config.add_field_mapping("platform_created_at", "date_created", "parse_woo_date")
    config.add_field_mapping("address_line_1", "billing.address_1")
    config.add_field_mapping("city", "billing.city")
    config.add_field_mapping("country", "billing.country")
    config.add_field_mapping("postal_code", "billing.postcode")
    
    # Order mappings
    config.add_field_mapping("order_number", "number")
    config.add_field_mapping("order_date", "date_created", "parse_woo_date")
    config.add_field_mapping("subtotal", "total", "decimal_conversion")
    config.add_field_mapping("tax_amount", "total_tax", "decimal_conversion")
    config.add_field_mapping("shipping_amount", "shipping_total", "decimal_conversion")
    config.add_field_mapping("total_amount", "total", "decimal_conversion")
    config.add_field_mapping("status", "status")
    config.add_field_mapping("currency", "currency")
    
    # Product mappings
    config.add_field_mapping("name", "name")
    config.add_field_mapping("description", "description", "strip_html")
    config.add_field_mapping("sku", "sku")
    config.add_field_mapping("price", "regular_price", "decimal_conversion")
    config.add_field_mapping("category", "categories.0.name")
    config.add_field_mapping("inventory_quantity", "stock_quantity")
    
    # Default values
    config.add_default_value("platform", "woocommerce")
    config.add_default_value("currency", "USD")
    
    return config


# Magento Configuration
def create_magento_config() -> PlatformConfig:
    """Configuration for Magento API/export format"""
    config = PlatformConfig("magento")
    
    # Customer mappings
    config.add_field_mapping("external_id", "entity_id")
    config.add_field_mapping("email", "email")
    config.add_field_mapping("first_name", "firstname")
    config.add_field_mapping("last_name", "lastname")
    config.add_field_mapping("platform_created_at", "created_at", "parse_magento_date")
    
    # Order mappings
    config.add_field_mapping("order_number", "increment_id")
    config.add_field_mapping("order_date", "created_at", "parse_magento_date")
    config.add_field_mapping("subtotal", "subtotal", "decimal_conversion")
    config.add_field_mapping("tax_amount", "tax_amount", "decimal_conversion")
    config.add_field_mapping("shipping_amount", "shipping_amount", "decimal_conversion")
    config.add_field_mapping("total_amount", "grand_total", "decimal_conversion")
    config.add_field_mapping("status", "status")
    
    # Default values
    config.add_default_value("platform", "magento")
    config.add_default_value("currency", "USD")
    
    return config


# Configuration Registry
PLATFORM_CONFIGS = {
    "generic_csv": create_generic_csv_config(),
    "shopify": create_shopify_config(),
    "woocommerce": create_woocommerce_config(),
    "magento": create_magento_config()
}


def get_platform_config(platform_name: str) -> PlatformConfig:
    """Get configuration for a specific platform"""
    if platform_name not in PLATFORM_CONFIGS:
        raise ValueError(f"Unsupported platform: {platform_name}. Supported platforms: {list(PLATFORM_CONFIGS.keys())}")
    
    return PLATFORM_CONFIGS[platform_name]


def list_supported_platforms() -> list:
    """List all supported platforms"""
    return list(PLATFORM_CONFIGS.keys())


def add_custom_platform_config(config: PlatformConfig):
    """Add a custom platform configuration"""
    PLATFORM_CONFIGS[config.platform_name] = config