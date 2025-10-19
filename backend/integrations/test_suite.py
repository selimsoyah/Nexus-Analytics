"""
Comprehensive Testing and Demo Suite for Nexus Analytics WooCommerce Integration
==============================================================================

Complete testing framework with unit tests, integration tests, and live demos
for all WooCommerce platform operations and multi-platform functionality.

Features:
- Unit tests for all connector components
- Integration tests for end-to-end workflows
- Demo scenarios with sample data
- Performance benchmarks
- Error simulation and recovery tests

Author: Nexus Analytics Team
Version: 1.0.0
"""

import unittest
import asyncio
import tempfile
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from .woocommerce_connector import WooCommerceConnector
from .woocommerce_schema_mapper import WooCommerceSchemaMapper
from .woocommerce_data_sync import WooCommerceDataSyncManager
from .platform_manager import PlatformIntegrationManager, PlatformType


# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWooCommerceConnector(unittest.TestCase):
    """Unit tests for WooCommerce connector"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_store_url = "https://test-store.example.com"
        self.test_consumer_key = "ck_test123"
        self.test_consumer_secret = "cs_test456"
        
        self.connector = WooCommerceConnector(
            store_url=self.test_store_url,
            consumer_key=self.test_consumer_key,
            consumer_secret=self.test_consumer_secret
        )
    
    def test_connector_initialization(self):
        """Test connector initialization"""
        self.assertEqual(self.connector.store_url, self.test_store_url)
        self.assertEqual(self.connector.consumer_key, self.test_consumer_key)
        self.assertEqual(self.connector.consumer_secret, self.test_consumer_secret)
        self.assertIsNotNone(self.connector.session)
    
    def test_url_validation(self):
        """Test URL validation and formatting"""
        # Test various URL formats
        test_cases = [
            ("http://example.com", "http://example.com"),
            ("https://example.com/", "https://example.com"),
            ("example.com", "https://example.com"),
        ]
        
        for input_url, expected_url in test_cases:
            connector = WooCommerceConnector(input_url, "key", "secret")
            self.assertEqual(connector.store_url, expected_url)
    
    def test_credential_validation(self):
        """Test credential validation"""
        # Test valid credentials
        self.assertTrue(self.connector._validate_credentials())
        
        # Test invalid credentials
        invalid_connector = WooCommerceConnector("", "", "")
        self.assertFalse(invalid_connector._validate_credentials())
    
    @patch('requests.Session.get')
    def test_api_request_success(self, mock_get):
        """Test successful API request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {"X-WP-TotalPages": "1"}
        mock_get.return_value = mock_response
        
        result = self.connector._make_request("products")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], {"success": True})
    
    @patch('requests.Session.get')
    def test_api_request_error(self, mock_get):
        """Test API request error handling"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        result = self.connector._make_request("invalid-endpoint")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("404", result["message"])
    
    def test_demo_data_generation(self):
        """Test demo data generation"""
        demo_data = WooCommerceConnector.generate_demo_data()
        
        self.assertIn("products", demo_data)
        self.assertIn("customers", demo_data)
        self.assertIn("orders", demo_data)
        
        # Check data structure
        self.assertGreater(len(demo_data["products"]), 0)
        self.assertGreater(len(demo_data["customers"]), 0)
        self.assertGreater(len(demo_data["orders"]), 0)


class TestWooCommerceSchemaMapper(unittest.TestCase):
    """Unit tests for WooCommerce schema mapper"""
    
    def setUp(self):
        """Set up test environment"""
        self.mapper = WooCommerceSchemaMapper()
    
    def test_order_mapping(self):
        """Test order data mapping"""
        sample_order = {
            "id": 12345,
            "status": "processing",
            "currency": "USD",
            "total": "99.99",
            "billing": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com"
            },
            "line_items": [
                {
                    "id": 1,
                    "name": "Test Product",
                    "quantity": 2,
                    "price": 49.99
                }
            ],
            "date_created": "2023-01-01T12:00:00"
        }
        
        universal_order = self.mapper.map_order_to_universal(sample_order)
        
        # Verify mapping
        self.assertEqual(universal_order["order_id"], "12345")
        self.assertEqual(universal_order["status"], "processing")
        self.assertEqual(universal_order["total_amount"], 99.99)
        self.assertEqual(universal_order["currency"], "USD")
        self.assertEqual(universal_order["customer_email"], "john@example.com")
        self.assertEqual(len(universal_order["items"]), 1)
    
    def test_customer_mapping(self):
        """Test customer data mapping"""
        sample_customer = {
            "id": 67890,
            "email": "jane@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "date_created": "2023-01-01T12:00:00",
            "orders_count": 5,
            "total_spent": "299.95"
        }
        
        universal_customer = self.mapper.map_customer_to_universal(sample_customer)
        
        # Verify mapping
        self.assertEqual(universal_customer["customer_id"], "67890")
        self.assertEqual(universal_customer["email"], "jane@example.com")
        self.assertEqual(universal_customer["full_name"], "Jane Smith")
        self.assertEqual(universal_customer["total_orders"], 5)
        self.assertEqual(universal_customer["total_spent"], 299.95)
    
    def test_product_mapping(self):
        """Test product data mapping"""
        sample_product = {
            "id": 11111,
            "name": "Amazing Widget",
            "sku": "AWG-001",
            "price": "29.99",
            "regular_price": "39.99",
            "sale_price": "29.99",
            "stock_quantity": 100,
            "categories": [{"name": "Widgets"}],
            "date_created": "2023-01-01T12:00:00"
        }
        
        universal_product = self.mapper.map_product_to_universal(sample_product)
        
        # Verify mapping
        self.assertEqual(universal_product["product_id"], "11111")
        self.assertEqual(universal_product["name"], "Amazing Widget")
        self.assertEqual(universal_product["sku"], "AWG-001")
        self.assertEqual(universal_product["price"], 29.99)
        self.assertEqual(universal_product["stock_quantity"], 100)
        self.assertEqual(universal_product["categories"], ["Widgets"])
    
    def test_batch_mapping(self):
        """Test batch data mapping"""
        sample_orders = [
            {"id": 1, "status": "completed", "total": "50.00"},
            {"id": 2, "status": "processing", "total": "75.00"}
        ]
        
        universal_orders = self.mapper.map_orders_to_universal(sample_orders)
        
        self.assertEqual(len(universal_orders), 2)
        self.assertEqual(universal_orders[0]["order_id"], "1")
        self.assertEqual(universal_orders[1]["order_id"], "2")


class TestWooCommerceDataSync(unittest.TestCase):
    """Unit tests for WooCommerce data synchronization"""
    
    def setUp(self):
        """Set up test environment"""
        self.sync_manager = WooCommerceDataSyncManager("test-store")
    
    def test_sync_manager_initialization(self):
        """Test sync manager initialization"""
        self.assertEqual(self.sync_manager.store_identifier, "test-store")
        self.assertEqual(self.sync_manager.batch_size, 50)
        self.assertEqual(self.sync_manager.max_workers, 3)
        self.assertFalse(self.sync_manager.is_syncing)
    
    def test_sync_status(self):
        """Test sync status reporting"""
        status = self.sync_manager.get_sync_status()
        
        self.assertIn("is_syncing", status)
        self.assertIn("connection_status", status)
        self.assertIn("last_sync", status)
        self.assertIn("sync_statistics", status)
    
    def test_sync_progress_tracking(self):
        """Test sync progress tracking"""
        # Start a mock sync
        self.sync_manager.is_syncing = True
        self.sync_manager.current_progress = {
            "stage": "products",
            "processed": 50,
            "total": 100,
            "percentage": 50.0
        }
        
        status = self.sync_manager.get_sync_status()
        
        self.assertTrue(status["is_syncing"])
        self.assertEqual(status["sync_statistics"]["stage"], "products")
        self.assertEqual(status["sync_statistics"]["percentage"], 50.0)


class TestPlatformIntegrationManager(unittest.TestCase):
    """Unit tests for platform integration manager"""
    
    def setUp(self):
        """Set up test environment"""
        # Use temporary directory for test configurations
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PlatformIntegrationManager(config_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        self.assertEqual(str(self.manager.config_dir), self.temp_dir)
        self.assertEqual(len(self.manager.platforms), 0)
        self.assertEqual(len(self.manager.connectors), 0)
    
    def test_platform_registration(self):
        """Test platform registration"""
        success = self.manager.register_platform(
            platform_id="test-woo-1",
            platform_type=PlatformType.WOOCOMMERCE,
            store_name="Test Store",
            api_endpoint="https://test.example.com",
            credentials={"consumer_key": "ck_test", "consumer_secret": "cs_test"}
        )
        
        self.assertTrue(success)
        self.assertEqual(len(self.manager.platforms), 1)
        self.assertIn("test-woo-1", self.manager.platforms)
    
    def test_platform_unregistration(self):
        """Test platform unregistration"""
        # Register a platform first
        self.manager.register_platform(
            platform_id="test-woo-2",
            platform_type=PlatformType.WOOCOMMERCE,
            store_name="Test Store 2",
            api_endpoint="https://test2.example.com",
            credentials={"consumer_key": "ck_test2", "consumer_secret": "cs_test2"}
        )
        
        # Unregister it
        success = self.manager.unregister_platform("test-woo-2")
        
        self.assertTrue(success)
        self.assertEqual(len(self.manager.platforms), 0)
    
    def test_platform_listing(self):
        """Test platform listing"""
        # Register multiple platforms
        platforms_to_register = [
            ("woo-1", PlatformType.WOOCOMMERCE, "WooCommerce Store"),
            ("shopify-1", PlatformType.SHOPIFY, "Shopify Store"),
        ]
        
        for platform_id, platform_type, store_name in platforms_to_register:
            self.manager.register_platform(
                platform_id=platform_id,
                platform_type=platform_type,
                store_name=store_name,
                api_endpoint=f"https://{platform_id}.example.com",
                credentials={"key": "value"}
            )
        
        platforms = self.manager.list_platforms()
        
        self.assertEqual(len(platforms), 2)
        self.assertIn("woo-1", platforms)
        self.assertIn("shopify-1", platforms)
    
    def test_analytics_generation(self):
        """Test analytics generation"""
        # Register some platforms
        self.manager.register_platform(
            "test-analytics",
            PlatformType.WOOCOMMERCE,
            "Analytics Test",
            "https://analytics.example.com",
            {"key": "value"}
        )
        
        analytics = self.manager.get_platform_analytics()
        
        self.assertIn("platform_summary", analytics)
        self.assertIn("sync_history", analytics)
        self.assertEqual(analytics["platform_summary"]["total_platforms"], 1)


class IntegrationTestSuite:
    """Integration tests for end-to-end workflows"""
    
    @staticmethod
    async def test_full_woocommerce_workflow():
        """Test complete WooCommerce integration workflow"""
        print("🔄 Running Full WooCommerce Integration Test")
        print("=" * 50)
        
        try:
            # 1. Test connector creation
            print("1️⃣ Testing Connector Creation...")
            connector = WooCommerceConnector(
                store_url="https://demo-integration-test.nexusanalytics.com",
                consumer_key="ck_integration_test",
                consumer_secret="cs_integration_test"
            )
            print("   ✅ Connector created successfully")
            
            # 2. Test schema mapper
            print("2️⃣ Testing Schema Mapping...")
            mapper = WooCommerceSchemaMapper()
            
            # Test with demo data
            demo_data = WooCommerceConnector.generate_demo_data()
            mapped_orders = mapper.map_orders_to_universal(demo_data["orders"])
            mapped_customers = mapper.map_customers_to_universal(demo_data["customers"])
            mapped_products = mapper.map_products_to_universal(demo_data["products"])
            
            print(f"   ✅ Mapped {len(mapped_orders)} orders")
            print(f"   ✅ Mapped {len(mapped_customers)} customers") 
            print(f"   ✅ Mapped {len(mapped_products)} products")
            
            # 3. Test data synchronization
            print("3️⃣ Testing Data Synchronization...")
            sync_manager = WooCommerceDataSyncManager("integration-test-store")
            
            # Test demo sync
            demo_result = await sync_manager.sync_demo_data()
            print(f"   ✅ Demo sync completed: {demo_result['status']}")
            
            # 4. Test platform manager integration
            print("4️⃣ Testing Platform Manager Integration...")
            temp_dir = tempfile.mkdtemp()
            platform_manager = PlatformIntegrationManager(config_dir=temp_dir)
            
            # Register WooCommerce platform
            registration_success = platform_manager.register_platform(
                platform_id="integration-test-woo",
                platform_type=PlatformType.WOOCOMMERCE,
                store_name="Integration Test Store",
                api_endpoint="https://integration-test.nexusanalytics.com",
                credentials={
                    "consumer_key": "ck_integration",
                    "consumer_secret": "cs_integration"
                }
            )
            
            print(f"   ✅ Platform registration: {'Success' if registration_success else 'Failed'}")
            
            # Get analytics
            analytics = platform_manager.get_platform_analytics()
            print(f"   ✅ Analytics generated: {analytics['platform_summary']['total_platforms']} platforms")
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            print("\\n🎉 Full Integration Test PASSED!")
            return True
            
        except Exception as e:
            print(f"\\n❌ Integration Test FAILED: {e}")
            return False
    
    @staticmethod
    async def test_multi_platform_workflow():
        """Test multi-platform integration workflow"""
        print("🔄 Running Multi-Platform Integration Test")
        print("=" * 50)
        
        try:
            # Create platform manager
            temp_dir = tempfile.mkdtemp()
            manager = PlatformIntegrationManager(config_dir=temp_dir)
            
            # Register multiple platforms
            platforms = [
                ("multi-woo-1", PlatformType.WOOCOMMERCE, "Multi WooCommerce 1"),
                ("multi-woo-2", PlatformType.WOOCOMMERCE, "Multi WooCommerce 2"),
                ("multi-shopify-1", PlatformType.SHOPIFY, "Multi Shopify 1"),
            ]
            
            print("1️⃣ Registering Multiple Platforms...")
            for platform_id, platform_type, store_name in platforms:
                success = manager.register_platform(
                    platform_id=platform_id,
                    platform_type=platform_type,
                    store_name=store_name,
                    api_endpoint=f"https://{platform_id}.example.com",
                    credentials={"key": "test", "secret": "test"}
                )
                print(f"   {'✅' if success else '❌'} {store_name}")
            
            # Test cross-platform operations
            print("2️⃣ Testing Cross-Platform Operations...")
            all_platforms = manager.list_platforms()
            print(f"   ✅ Listed {len(all_platforms)} platforms")
            
            # Test connection testing
            print("3️⃣ Testing Connection Tests...")
            connection_results = await manager.test_all_connections()
            successful_connections = sum(1 for success in connection_results.values() if success)
            print(f"   ✅ Connection tests: {successful_connections}/{len(connection_results)} successful")
            
            # Test sync summary
            print("4️⃣ Testing Cross-Platform Sync...")
            sync_summary = await manager.sync_all_platforms()
            print(f"   ✅ Sync completed: {sync_summary.successful_syncs}/{sync_summary.total_platforms}")
            
            # Test analytics
            analytics = manager.get_platform_analytics()
            print(f"   ✅ Analytics: {analytics['platform_summary']['total_platforms']} total platforms")
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            print("\\n🎉 Multi-Platform Test PASSED!")
            return True
            
        except Exception as e:
            print(f"\\n❌ Multi-Platform Test FAILED: {e}")
            return False


class PerformanceBenchmarks:
    """Performance benchmarks for WooCommerce operations"""
    
    @staticmethod
    async def benchmark_data_processing():
        """Benchmark data processing performance"""
        print("⚡ Running Performance Benchmarks")
        print("=" * 40)
        
        # Test schema mapping performance
        print("📊 Schema Mapping Performance...")
        mapper = WooCommerceSchemaMapper()
        
        # Generate large dataset
        demo_data = WooCommerceConnector.generate_demo_data()
        large_orders = demo_data["orders"] * 100  # 1000+ orders
        
        start_time = datetime.now()
        mapped_orders = mapper.map_orders_to_universal(large_orders)
        mapping_time = (datetime.now() - start_time).total_seconds()
        
        print(f"   ✅ Mapped {len(mapped_orders)} orders in {mapping_time:.2f}s")
        print(f"   ⚡ Rate: {len(mapped_orders) / mapping_time:.0f} orders/second")
        
        # Test sync manager performance
        print("🔄 Sync Manager Performance...")
        sync_manager = WooCommerceDataSyncManager("benchmark-store")
        
        start_time = datetime.now()
        demo_result = await sync_manager.sync_demo_data()
        sync_time = (datetime.now() - start_time).total_seconds()
        
        print(f"   ✅ Demo sync completed in {sync_time:.2f}s")
        if demo_result.get("sync_statistics"):
            stats = demo_result["sync_statistics"]
            total_records = sum(v for k, v in stats.items() if k.endswith("_created"))
            print(f"   ⚡ Rate: {total_records / sync_time:.0f} records/second")
        
        return {
            "mapping_rate": len(mapped_orders) / mapping_time,
            "sync_time": sync_time,
            "total_orders_mapped": len(mapped_orders)
        }


# Demo scenarios
class DemoScenarios:
    """Interactive demo scenarios"""
    
    @staticmethod
    async def ecommerce_analytics_demo():
        """Comprehensive e-commerce analytics demo"""
        print("🛍️ E-Commerce Analytics Demo")
        print("=" * 35)
        
        # Create demo setup
        temp_dir = tempfile.mkdtemp()
        manager = PlatformIntegrationManager(config_dir=temp_dir)
        
        # Register demo stores
        stores = [
            ("fashion-store", "Fashion Boutique"),
            ("electronics-store", "Electronics Hub"),
            ("books-store", "Book Paradise")
        ]
        
        print("🏪 Setting up Demo Stores...")
        for store_id, store_name in stores:
            success = manager.register_platform(
                platform_id=store_id,
                platform_type=PlatformType.WOOCOMMERCE,
                store_name=store_name,
                api_endpoint=f"https://{store_id}.nexusanalytics.com",
                credentials={"consumer_key": f"ck_{store_id}", "consumer_secret": f"cs_{store_id}"}
            )
            print(f"   {'✅' if success else '❌'} {store_name}")
        
        # Simulate data sync
        print("\\n🔄 Synchronizing Store Data...")
        sync_summary = await manager.sync_all_platforms()
        
        print(f"   📊 Sync Results:")
        print(f"      Total Stores: {sync_summary.total_platforms}")
        print(f"      Successful: {sync_summary.successful_syncs}")
        print(f"      Duration: {sync_summary.sync_duration:.1f}s")
        
        # Generate analytics
        print("\\n📈 Generating Analytics...")
        analytics = manager.get_platform_analytics()
        
        print(f"   🎯 Platform Summary:")
        summary = analytics["platform_summary"]
        print(f"      Active Platforms: {summary['active_platforms']}/{summary['total_platforms']}")
        print(f"      Platform Types: {summary['platform_types']}")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        print("\\n✨ Demo Complete! Ready for production deployment.")
        return analytics


# Test runner functions
async def run_all_tests():
    """Run complete test suite"""
    print("🧪 Running Complete Test Suite for WooCommerce Integration")
    print("=" * 65)
    
    test_results = {
        "unit_tests": {},
        "integration_tests": {},
        "performance_tests": {},
        "demo_scenarios": {}
    }
    
    # Run unit tests
    print("\\n1️⃣ UNIT TESTS")
    print("-" * 20)
    
    test_classes = [
        TestWooCommerceConnector,
        TestWooCommerceSchemaMapper,
        TestWooCommerceDataSync,
        TestPlatformIntegrationManager
    ]
    
    for test_class in test_classes:
        print(f"Testing {test_class.__name__}...")
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
        result = runner.run(suite)
        
        success = result.wasSuccessful()
        test_results["unit_tests"][test_class.__name__] = {
            "success": success,
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors)
        }
        
        print(f"   {'✅' if success else '❌'} {test_class.__name__}: {result.testsRun} tests")
    
    # Run integration tests
    print("\\n2️⃣ INTEGRATION TESTS")
    print("-" * 25)
    
    integration_suite = IntegrationTestSuite()
    
    woocommerce_result = await integration_suite.test_full_woocommerce_workflow()
    test_results["integration_tests"]["woocommerce_workflow"] = woocommerce_result
    
    multiplatform_result = await integration_suite.test_multi_platform_workflow()
    test_results["integration_tests"]["multiplatform_workflow"] = multiplatform_result
    
    # Run performance benchmarks
    print("\\n3️⃣ PERFORMANCE BENCHMARKS")
    print("-" * 30)
    
    benchmarks = PerformanceBenchmarks()
    perf_results = await benchmarks.benchmark_data_processing()
    test_results["performance_tests"] = perf_results
    
    # Run demo scenarios
    print("\\n4️⃣ DEMO SCENARIOS")
    print("-" * 20)
    
    demo = DemoScenarios()
    demo_results = await demo.ecommerce_analytics_demo()
    test_results["demo_scenarios"] = demo_results
    
    # Summary
    print("\\n" + "="*65)
    print("🎉 TEST SUITE COMPLETE")
    print("="*65)
    
    unit_success = all(result["success"] for result in test_results["unit_tests"].values())
    integration_success = all(test_results["integration_tests"].values())
    
    print(f"Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
    print(f"Integration Tests: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    print(f"Performance: ⚡ {perf_results['mapping_rate']:.0f} orders/sec mapping rate")
    print(f"Demo Scenarios: ✅ COMPLETED")
    
    overall_success = unit_success and integration_success
    print(f"\\nOVERALL RESULT: {'🎉 ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return test_results


if __name__ == "__main__":
    # Run all tests when executed directly
    asyncio.run(run_all_tests())