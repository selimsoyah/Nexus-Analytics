"""
Test Script for Modular ETL System

This script tests the new modular ETL system with our existing CSV data
to ensure everything works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connectors.modular_etl import ModularETL, quick_csv_ingestion, preview_csv_transformation
from connectors.platform_configs import list_supported_platforms


def test_modular_etl():
    """Test the modular ETL system"""
    
    print("🧪 Testing Modular ETL System")
    print("=" * 50)
    
    # Database connection
    DB_URL = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"
    
    # Initialize ETL engine
    etl = ModularETL(DB_URL)
    
    # Test 1: List supported platforms
    print("📋 Supported Platforms:")
    platforms = list_supported_platforms()
    for platform in platforms:
        print(f"  ✓ {platform}")
    print()
    
    # Test 2: Preview transformations
    print("🔍 Previewing CSV Transformation (generic_csv platform):")
    preview = etl.preview_ingestion(
        platform="generic_csv",
        data_source="customers.csv",
        data_type="customers"
    )
    
    if preview['success']:
        print("  ✓ Preview successful!")
        print(f"  📊 Sample transformation:")
        for i, (original, transformed) in enumerate(zip(
            preview['preview']['sample_transformation']['original'],
            preview['preview']['sample_transformation']['transformed']
        )):
            print(f"    Record {i+1}:")
            print(f"      Original: {original}")
            print(f"      Transformed: {transformed}")
            print()
    else:
        print(f"  ❌ Preview failed: {preview['error']}")
    
    # Test 3: Test ingestion with new system
    print("📥 Testing Modular Ingestion:")
    
    # Ingest customers
    result = etl.ingest_platform_data(
        platform="generic_csv",
        data_source="customers.csv", 
        data_type="customers"
    )
    
    if result['success']:
        print(f"  ✓ Customers: {result['records_inserted']} records inserted")
    else:
        print(f"  ❌ Customers failed: {result['error']}")
    
    # Ingest orders
    result = etl.ingest_platform_data(
        platform="generic_csv",
        data_source="orders.csv",
        data_type="orders"
    )
    
    if result['success']:
        print(f"  ✓ Orders: {result['records_inserted']} records inserted")
    else:
        print(f"  ❌ Orders failed: {result['error']}")
    
    # Ingest order items
    result = etl.ingest_platform_data(
        platform="generic_csv",
        data_source="order_items.csv",
        data_type="order_items"
    )
    
    if result['success']:
        print(f"  ✓ Order Items: {result['records_inserted']} records inserted")
    else:
        print(f"  ❌ Order Items failed: {result['error']}")
    
    # Test 4: Get ingestion statistics
    print("📊 Ingestion Statistics:")
    stats = etl.get_ingestion_stats()
    for table, platform_counts in stats.items():
        print(f"  {table}:")
        if 'error' in platform_counts:
            print(f"    ❌ Error: {platform_counts['error']}")
        else:
            for platform, count in platform_counts.items():
                print(f"    {platform}: {count} records")
    print()
    
    # Test 5: Cross-platform analytics
    print("🔗 Cross-Platform Analytics:")
    analytics = etl.cross_platform_analytics()
    
    if 'error' in analytics:
        print(f"  ❌ Error: {analytics['error']}")
    else:
        print("  📈 Customers by Platform:")
        for platform, data in analytics.get('customers_by_platform', {}).items():
            print(f"    {platform}: {data['count']} customers, ${data['revenue']:.2f} revenue")
        
        print("  🏆 Top Products:")
        for product in analytics.get('top_products', [])[:5]:
            print(f"    {product['name']} ({product['platform']}): {product['units_sold']} units, ${product['revenue']:.2f}")
    
    print()
    print("✅ Modular ETL Test Complete!")


if __name__ == "__main__":
    test_modular_etl()