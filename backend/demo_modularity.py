"""
Simple Demo: Modular ETL in Action

This script demonstrates how our new modular system works across different platforms.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from connectors.modular_etl import ModularETL
from connectors.platform_configs import get_platform_config


def demonstrate_modularity():
    """Show how the same system handles different platform data"""
    
    print("🎯 Modular E-commerce Analytics Demo")
    print("=" * 50)
    
    # Create some sample data for different platforms
    
    # 1. Generic CSV format (current)
    generic_customers = pd.DataFrame([
        {"customer_id": 1, "customer_name": "John Doe", "email": "john@example.com"},
        {"customer_id": 2, "customer_name": "Jane Smith", "email": "jane@example.com"}
    ])
    
    # 2. Shopify format (hypothetical)
    shopify_customers = pd.DataFrame([
        {"id": "shop_001", "first_name": "Mike", "last_name": "Wilson", "email": "mike@shop.com", "total_spent": "250.00"},
        {"id": "shop_002", "first_name": "Sarah", "last_name": "Johnson", "email": "sarah@shop.com", "total_spent": "180.00"}
    ])
    
    # 3. WooCommerce format (hypothetical)
    woo_customers = pd.DataFrame([
        {"id": "woo_100", "first_name": "Bob", "last_name": "Brown", "email": "bob@woo.com"},
        {"id": "woo_101", "first_name": "Alice", "last_name": "Green", "email": "alice@woo.com"}
    ])
    
    # Initialize ETL (using in-memory database for demo)
    etl = ModularETL("sqlite:///:memory:")
    etl.create_universal_tables()
    
    print("📊 Platform Configurations Available:")
    platforms = ["generic_csv", "shopify", "woocommerce", "magento"]
    for platform in platforms:
        config = get_platform_config(platform)
        print(f"  ✓ {platform}: {len(config.field_mappings)} field mappings")
    print()
    
    print("🔄 Transforming Data from Different Platforms:")
    
    # Transform each platform's data
    datasets = [
        ("generic_csv", generic_customers),
        ("shopify", shopify_customers), 
        ("woocommerce", woo_customers)
    ]
    
    all_universal_data = []
    
    for platform, data in datasets:
        print(f"\n📈 Processing {platform} data:")
        print(f"  Original columns: {list(data.columns)}")
        
        # Transform using modular mapper
        universal_data = etl.multi_mapper.transform_data(platform, data, "customers")
        print(f"  Universal columns: {list(universal_data.columns)}")
        print(f"  Records: {len(universal_data)}")
        
        # Show sample transformation
        if len(universal_data) > 0:
            sample = universal_data.iloc[0]
            print(f"  Sample: {sample['first_name']} {sample['last_name']} ({sample['email']}) from {sample['platform']}")
        
        all_universal_data.append(universal_data)
    
    # Combine all data
    print("\n🔗 Combined Universal Data:")
    combined = pd.concat(all_universal_data, ignore_index=True)
    print(f"  Total customers from all platforms: {len(combined)}")
    
    platform_counts = combined['platform'].value_counts()
    for platform, count in platform_counts.items():
        print(f"    {platform}: {count} customers")
    
    print("\n✨ Key Benefits Demonstrated:")
    print("  🎯 Unified Schema: All platforms use same data structure")
    print("  🔧 Configurable Mapping: Each platform has its own transformation rules") 
    print("  📊 Cross-Platform Analytics: Can analyze data from all platforms together")
    print("  🚀 Easy Onboarding: New platforms just need a configuration file")
    
    print("\n🎉 Modular System Working Successfully!")


if __name__ == "__main__":
    demonstrate_modularity()