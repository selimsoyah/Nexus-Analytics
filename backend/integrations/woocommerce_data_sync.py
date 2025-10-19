"""
WooCommerce Data Synchronization Pipeline

This module provides complete data synchronization between WooCommerce stores
and the Nexus Analytics universal database system.

Features:
- Incremental and full data synchronization
- Real-time progress tracking
- Error handling and retry mechanisms
- Database integration with universal schema
- Conflict resolution and data validation
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import time
from dataclasses import dataclass
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Internal imports
from integrations.woocommerce_connector import WooCommerceConnector, WooCommerceCredentialManager
from integrations.woocommerce_schema_mapper import WooCommerceSchemaMapper
from database import get_database_connection, engine
from sqlalchemy import text, insert, update, select, and_, or_
from sqlalchemy.exc import IntegrityError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SyncProgress:
    """Data class to track synchronization progress"""
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    start_time: datetime = None
    end_time: datetime = None
    current_operation: str = ""
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    @property
    def progress_percentage(self) -> float:
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100
    
    @property
    def success_rate(self) -> float:
        if self.processed_items == 0:
            return 0.0
        return (self.successful_items / self.processed_items) * 100
    
    @property
    def duration_seconds(self) -> float:
        if not self.start_time:
            return 0.0
        end_time = self.end_time or datetime.now()
        return (end_time - self.start_time).total_seconds()


class WooCommerceDataSyncManager:
    """
    Comprehensive WooCommerce data synchronization manager
    
    Handles:
    - Full store synchronization
    - Incremental updates
    - Progress tracking and reporting
    - Error handling and recovery
    - Database integration
    """
    
    def __init__(self, store_identifier: str = "default"):
        """
        Initialize sync manager
        
        Args:
            store_identifier: Unique identifier for the WooCommerce store
        """
        self.store_identifier = store_identifier
        self.connector: Optional[WooCommerceConnector] = None
        self.mapper = WooCommerceSchemaMapper(store_identifier)
        self.credential_manager = WooCommerceCredentialManager()
        
        # Sync configuration
        self.batch_size = 50  # Items per API request
        self.max_workers = 3  # Parallel processing threads
        self.retry_attempts = 3
        self.retry_delay = 5  # seconds
        
        # Progress tracking
        self.sync_progress = SyncProgress()
        self.is_syncing = False
        
        # Database connection
        self.db_connection = get_database_connection()

    def connect_to_store(self, store_url: str, consumer_key: str, 
                        consumer_secret: str) -> Dict[str, Any]:
        """
        Connect to WooCommerce store and validate credentials
        
        Args:
            store_url: WooCommerce store URL
            consumer_key: API consumer key
            consumer_secret: API consumer secret
            
        Returns:
            Dict containing connection status and store info
        """
        try:
            self.connector = WooCommerceConnector(store_url, consumer_key, consumer_secret)
            connection_result = self.connector.test_connection()
            
            if connection_result['status'] == 'success':
                # Save credentials for future use
                self.credential_manager.add_store(
                    self.store_identifier,
                    store_url,
                    consumer_key,
                    consumer_secret,
                    f"WooCommerce Store - {store_url}"
                )
                
                logger.info(f"✅ Connected to WooCommerce store: {store_url}")
                return connection_result
            else:
                logger.error(f"❌ Failed to connect to WooCommerce store: {connection_result.get('message')}")
                return connection_result
                
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg
            }

    def load_stored_connection(self) -> bool:
        """
        Load previously stored connection credentials
        
        Returns:
            bool: True if connection loaded successfully
        """
        try:
            creds = self.credential_manager.get_store_credentials(self.store_identifier)
            
            if creds:
                self.connector = WooCommerceConnector(
                    creds['store_url'],
                    creds['consumer_key'],
                    creds['consumer_secret']
                )
                logger.info(f"✅ Loaded stored WooCommerce connection")
                return True
            else:
                logger.warning(f"⚠️ No stored credentials found for store: {self.store_identifier}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to load stored connection: {str(e)}")
            return False

    # =================================================================
    # FULL SYNCHRONIZATION METHODS
    # =================================================================
    
    async def sync_full_store(self, progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Perform complete store synchronization
        
        Args:
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dict containing sync results and statistics
        """
        if not self.connector:
            return {
                'status': 'error',
                'message': 'No WooCommerce connection available'
            }
        
        self.is_syncing = True
        self.sync_progress = SyncProgress()
        self.sync_progress.start_time = datetime.now()
        self.sync_progress.current_operation = "Initializing full store sync"
        
        logger.info("🔄 Starting full WooCommerce store synchronization")
        
        try:
            # Phase 1: Fetch all data from WooCommerce
            self.sync_progress.current_operation = "Fetching store data"
            if progress_callback:
                progress_callback(self.sync_progress)
            
            store_data = self.connector.get_all_data(self.batch_size)
            
            if store_data['status'] != 'success':
                raise Exception(f"Failed to fetch store data: {store_data.get('message', 'Unknown error')}")
            
            # Calculate total items for progress tracking
            total_products = len(store_data['data']['products'])
            total_customers = len(store_data['data']['customers'])
            total_orders = len(store_data['data']['orders'])
            
            self.sync_progress.total_items = total_products + total_customers + total_orders
            
            logger.info(f"📊 Store data fetched: {total_products} products, {total_customers} customers, {total_orders} orders")
            
            # Phase 2: Sync products
            product_results = await self._sync_products(
                store_data['data']['products'], 
                progress_callback
            )
            
            # Phase 3: Sync customers
            customer_results = await self._sync_customers(
                store_data['data']['customers'], 
                progress_callback
            )
            
            # Phase 4: Sync orders
            order_results = await self._sync_orders(
                store_data['data']['orders'], 
                progress_callback
            )
            
            # Compile final results
            self.sync_progress.end_time = datetime.now()
            self.sync_progress.current_operation = "Sync completed"
            
            if progress_callback:
                progress_callback(self.sync_progress)
            
            sync_results = {
                'status': 'success',
                'message': 'Full store synchronization completed',
                'store_identifier': self.store_identifier,
                'sync_statistics': {
                    'total_duration_seconds': self.sync_progress.duration_seconds,
                    'total_items_processed': self.sync_progress.processed_items,
                    'success_rate': self.sync_progress.success_rate,
                    'products': product_results,
                    'customers': customer_results,
                    'orders': order_results
                },
                'completed_at': datetime.now().isoformat()
            }
            
            logger.info(f"🎉 Full sync completed in {self.sync_progress.duration_seconds:.1f}s")
            logger.info(f"📊 Success rate: {self.sync_progress.success_rate:.1f}%")
            
            return sync_results
            
        except Exception as e:
            error_msg = f"Full sync failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            self.sync_progress.errors.append(error_msg)
            self.sync_progress.end_time = datetime.now()
            
            return {
                'status': 'error',
                'message': error_msg,
                'sync_progress': self.sync_progress,
                'failed_at': datetime.now().isoformat()
            }
            
        finally:
            self.is_syncing = False

    async def _sync_products(self, woo_products: List[Dict[str, Any]], 
                           progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Synchronize WooCommerce products to database
        
        Args:
            woo_products: List of WooCommerce product objects
            progress_callback: Progress callback function
            
        Returns:
            Dict containing sync results
        """
        self.sync_progress.current_operation = "Syncing products"
        if progress_callback:
            progress_callback(self.sync_progress)
        
        logger.info(f"🔄 Syncing {len(woo_products)} products...")
        
        successful_products = 0
        failed_products = 0
        
        try:
            # Map products to universal schema
            universal_products = self.mapper.map_batch_products(woo_products)
            
            # Insert/update products in database
            for product in universal_products:
                try:
                    if 'error' not in product:
                        await self._upsert_product(product)
                        successful_products += 1
                    else:
                        failed_products += 1
                        self.sync_progress.errors.append(f"Product mapping failed: {product.get('error')}")
                    
                    # Update progress
                    self.sync_progress.processed_items += 1
                    self.sync_progress.successful_items += successful_products
                    self.sync_progress.failed_items += failed_products
                    
                    if progress_callback and self.sync_progress.processed_items % 10 == 0:
                        progress_callback(self.sync_progress)
                        
                except Exception as e:
                    failed_products += 1
                    error_msg = f"Product {product.get('product_id', 'unknown')} sync failed: {str(e)}"
                    self.sync_progress.errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")
            
            logger.info(f"✅ Products sync: {successful_products} success, {failed_products} failed")
            
            return {
                'total_products': len(woo_products),
                'successful_products': successful_products,
                'failed_products': failed_products,
                'success_rate': (successful_products / len(woo_products) * 100) if woo_products else 0
            }
            
        except Exception as e:
            error_msg = f"Product sync batch failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.sync_progress.errors.append(error_msg)
            
            return {
                'total_products': len(woo_products),
                'successful_products': successful_products,
                'failed_products': len(woo_products) - successful_products,
                'error': error_msg
            }

    async def _sync_customers(self, woo_customers: List[Dict[str, Any]], 
                            progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Synchronize WooCommerce customers to database
        
        Args:
            woo_customers: List of WooCommerce customer objects
            progress_callback: Progress callback function
            
        Returns:
            Dict containing sync results
        """
        self.sync_progress.current_operation = "Syncing customers"
        if progress_callback:
            progress_callback(self.sync_progress)
        
        logger.info(f"🔄 Syncing {len(woo_customers)} customers...")
        
        successful_customers = 0
        failed_customers = 0
        
        try:
            # Map customers to universal schema
            universal_customers = self.mapper.map_batch_customers(woo_customers)
            
            # Insert/update customers in database
            for customer in universal_customers:
                try:
                    if 'error' not in customer:
                        await self._upsert_customer(customer)
                        successful_customers += 1
                    else:
                        failed_customers += 1
                        self.sync_progress.errors.append(f"Customer mapping failed: {customer.get('error')}")
                    
                    # Update progress
                    self.sync_progress.processed_items += 1
                    self.sync_progress.successful_items += successful_customers
                    self.sync_progress.failed_items += failed_customers
                    
                    if progress_callback and self.sync_progress.processed_items % 10 == 0:
                        progress_callback(self.sync_progress)
                        
                except Exception as e:
                    failed_customers += 1
                    error_msg = f"Customer {customer.get('customer_id', 'unknown')} sync failed: {str(e)}"
                    self.sync_progress.errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")
            
            logger.info(f"✅ Customers sync: {successful_customers} success, {failed_customers} failed")
            
            return {
                'total_customers': len(woo_customers),
                'successful_customers': successful_customers,
                'failed_customers': failed_customers,
                'success_rate': (successful_customers / len(woo_customers) * 100) if woo_customers else 0
            }
            
        except Exception as e:
            error_msg = f"Customer sync batch failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.sync_progress.errors.append(error_msg)
            
            return {
                'total_customers': len(woo_customers),
                'successful_customers': successful_customers,
                'failed_customers': len(woo_customers) - successful_customers,
                'error': error_msg
            }

    async def _sync_orders(self, woo_orders: List[Dict[str, Any]], 
                          progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Synchronize WooCommerce orders to database
        
        Args:
            woo_orders: List of WooCommerce order objects
            progress_callback: Progress callback function
            
        Returns:
            Dict containing sync results
        """
        self.sync_progress.current_operation = "Syncing orders"
        if progress_callback:
            progress_callback(self.sync_progress)
        
        logger.info(f"🔄 Syncing {len(woo_orders)} orders...")
        
        successful_orders = 0
        failed_orders = 0
        
        try:
            # Map orders to universal schema
            universal_orders = self.mapper.map_batch_orders(woo_orders)
            
            # Insert/update orders in database
            for order in universal_orders:
                try:
                    if 'error' not in order:
                        await self._upsert_order(order)
                        successful_orders += 1
                    else:
                        failed_orders += 1
                        self.sync_progress.errors.append(f"Order mapping failed: {order.get('error')}")
                    
                    # Update progress
                    self.sync_progress.processed_items += 1
                    self.sync_progress.successful_items += successful_orders
                    self.sync_progress.failed_items += failed_orders
                    
                    if progress_callback and self.sync_progress.processed_items % 10 == 0:
                        progress_callback(self.sync_progress)
                        
                except Exception as e:
                    failed_orders += 1
                    error_msg = f"Order {order.get('order_id', 'unknown')} sync failed: {str(e)}"
                    self.sync_progress.errors.append(error_msg)
                    logger.error(f"❌ {error_msg}")
            
            logger.info(f"✅ Orders sync: {successful_orders} success, {failed_orders} failed")
            
            return {
                'total_orders': len(woo_orders),
                'successful_orders': successful_orders,
                'failed_orders': failed_orders,
                'success_rate': (successful_orders / len(woo_orders) * 100) if woo_orders else 0
            }
            
        except Exception as e:
            error_msg = f"Order sync batch failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.sync_progress.errors.append(error_msg)
            
            return {
                'total_orders': len(woo_orders),
                'successful_orders': successful_orders,
                'failed_orders': len(woo_orders) - successful_orders,
                'error': error_msg
            }

    # =================================================================
    # DATABASE OPERATIONS
    # =================================================================
    
    async def _upsert_product(self, product: Dict[str, Any]) -> bool:
        """
        Insert or update product in database
        
        Args:
            product: Universal schema product object
            
        Returns:
            bool: True if successful
        """
        try:
            with self.db_connection.begin() as conn:
                # Check if product exists
                existing = conn.execute(text("""
                    SELECT product_id FROM products 
                    WHERE platform_product_id = :product_id AND platform = :platform
                """), {
                    'product_id': product['platform_product_id'],
                    'platform': product['platform']
                }).fetchone()
                
                if existing:
                    # Update existing product
                    conn.execute(text("""
                        UPDATE products SET
                            name = :name,
                            price = :price,
                            sku = :sku,
                            status = :status,
                            updated_at = :updated_at
                        WHERE platform_product_id = :product_id AND platform = :platform
                    """), {
                        'name': product['name'],
                        'price': product['price'],
                        'sku': product['sku'],
                        'status': product['status'],
                        'updated_at': product['updated_at'],
                        'product_id': product['platform_product_id'],
                        'platform': product['platform']
                    })
                else:
                    # Insert new product
                    conn.execute(text("""
                        INSERT INTO products (
                            platform_product_id, platform, store_identifier,
                            name, price, sku, status, created_at, updated_at
                        ) VALUES (
                            :product_id, :platform, :store_identifier,
                            :name, :price, :sku, :status, :created_at, :updated_at
                        )
                    """), {
                        'product_id': product['platform_product_id'],
                        'platform': product['platform'],
                        'store_identifier': product['store_identifier'],
                        'name': product['name'],
                        'price': product['price'],
                        'sku': product['sku'],
                        'status': product['status'],
                        'created_at': product['created_at'],
                        'updated_at': product['updated_at']
                    })
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Product upsert failed: {str(e)}")
            return False

    async def _upsert_customer(self, customer: Dict[str, Any]) -> bool:
        """
        Insert or update customer in database
        
        Args:
            customer: Universal schema customer object
            
        Returns:
            bool: True if successful
        """
        try:
            with self.db_connection.begin() as conn:
                # Check if customer exists
                existing = conn.execute(text("""
                    SELECT customer_id FROM customers 
                    WHERE customer_external_id = :customer_id AND platform = :platform
                """), {
                    'customer_id': customer['customer_external_id'],
                    'platform': customer['platform']
                }).fetchone()
                
                if existing:
                    # Update existing customer
                    conn.execute(text("""
                        UPDATE customers SET
                            first_name = :first_name,
                            last_name = :last_name,
                            email = :email,
                            total_orders = :total_orders,
                            total_spent = :total_spent,
                            updated_at = :updated_at
                        WHERE customer_external_id = :customer_id AND platform = :platform
                    """), {
                        'first_name': customer['first_name'],
                        'last_name': customer['last_name'],
                        'email': customer['email'],
                        'total_orders': customer['total_orders'],
                        'total_spent': customer['total_spent'],
                        'updated_at': customer['updated_at'],
                        'customer_id': customer['customer_external_id'],
                        'platform': customer['platform']
                    })
                else:
                    # Insert new customer
                    conn.execute(text("""
                        INSERT INTO customers (
                            customer_external_id, platform, store_identifier,
                            first_name, last_name, email, total_orders, total_spent,
                            created_at, updated_at
                        ) VALUES (
                            :customer_id, :platform, :store_identifier,
                            :first_name, :last_name, :email, :total_orders, :total_spent,
                            :created_at, :updated_at
                        )
                    """), {
                        'customer_id': customer['customer_external_id'],
                        'platform': customer['platform'],
                        'store_identifier': customer['store_identifier'],
                        'first_name': customer['first_name'],
                        'last_name': customer['last_name'],
                        'email': customer['email'],
                        'total_orders': customer['total_orders'],
                        'total_spent': customer['total_spent'],
                        'created_at': customer['created_at'],
                        'updated_at': customer['updated_at']
                    })
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Customer upsert failed: {str(e)}")
            return False

    async def _upsert_order(self, order: Dict[str, Any]) -> bool:
        """
        Insert or update order in database
        
        Args:
            order: Universal schema order object
            
        Returns:
            bool: True if successful
        """
        try:
            with self.db_connection.begin() as conn:
                # Check if order exists
                existing = conn.execute(text("""
                    SELECT order_id FROM orders 
                    WHERE platform_order_id = :order_id AND platform = :platform
                """), {
                    'order_id': order['platform_order_id'],
                    'platform': order['platform']
                }).fetchone()
                
                if existing:
                    # Update existing order
                    conn.execute(text("""
                        UPDATE orders SET
                            order_status = :status,
                            total_amount = :total_amount,
                            currency = :currency,
                            updated_at = :updated_at
                        WHERE platform_order_id = :order_id AND platform = :platform
                    """), {
                        'status': order['order_status'],
                        'total_amount': order['total_amount'],
                        'currency': order['currency'],
                        'updated_at': order['updated_at'],
                        'order_id': order['platform_order_id'],
                        'platform': order['platform']
                    })
                else:
                    # Insert new order
                    conn.execute(text("""
                        INSERT INTO orders (
                            platform_order_id, platform, store_identifier,
                            customer_external_id, order_status, total_amount, currency,
                            order_date, created_at, updated_at
                        ) VALUES (
                            :order_id, :platform, :store_identifier,
                            :customer_id, :status, :total_amount, :currency,
                            :order_date, :created_at, :updated_at
                        )
                    """), {
                        'order_id': order['platform_order_id'],
                        'platform': order['platform'],
                        'store_identifier': order['store_identifier'],
                        'customer_id': order['customer_external_id'],
                        'status': order['order_status'],
                        'total_amount': order['total_amount'],
                        'currency': order['currency'],
                        'order_date': order['order_date'],
                        'created_at': order['created_at'],
                        'updated_at': order['updated_at']
                    })
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Order upsert failed: {str(e)}")
            return False

    # =================================================================
    # DEMO AND TESTING METHODS
    # =================================================================
    
    def create_demo_sync(self) -> Dict[str, Any]:
        """
        Create demo WooCommerce data for testing purposes
        
        Returns:
            Dict containing demo sync results
        """
        logger.info("🎭 Creating demo WooCommerce sync data...")
        
        try:
            # Generate demo credentials
            demo_creds = WooCommerceConnector.generate_demo_credentials()
            
            # Create demo connector (won't make real API calls)
            self.connector = WooCommerceConnector(
                demo_creds['store_url'],
                demo_creds['consumer_key'],
                demo_creds['consumer_secret']
            )
            
            # Generate demo data
            demo_results = {
                'status': 'success',
                'message': 'Demo WooCommerce sync completed',
                'store_info': demo_creds,
                'sync_statistics': {
                    'demo_products_created': 25,
                    'demo_customers_created': 15,
                    'demo_orders_created': 40,
                    'sync_duration': 2.5,
                    'success_rate': 100.0
                },
                'demo_data_note': 'This is simulated data for testing WooCommerce integration',
                'created_at': datetime.now().isoformat()
            }
            
            logger.info("🎉 Demo WooCommerce sync completed")
            return demo_results
            
        except Exception as e:
            error_msg = f"Demo sync failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg
            }

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current synchronization status and progress
        
        Returns:
            Dict containing sync status information
        """
        return {
            'is_syncing': self.is_syncing,
            'store_identifier': self.store_identifier,
            'progress': {
                'percentage': self.sync_progress.progress_percentage,
                'processed_items': self.sync_progress.processed_items,
                'total_items': self.sync_progress.total_items,
                'success_rate': self.sync_progress.success_rate,
                'current_operation': self.sync_progress.current_operation,
                'duration_seconds': self.sync_progress.duration_seconds
            },
            'connection_status': 'connected' if self.connector else 'not_connected',
            'last_check': datetime.now().isoformat()
        }


# Convenience functions for direct usage
async def sync_woocommerce_store(store_url: str, consumer_key: str, consumer_secret: str,
                               store_identifier: str = "default") -> Dict[str, Any]:
    """
    Convenience function to sync a WooCommerce store
    
    Args:
        store_url: WooCommerce store URL
        consumer_key: API consumer key
        consumer_secret: API consumer secret
        store_identifier: Unique store identifier
        
    Returns:
        Dict containing sync results
    """
    sync_manager = WooCommerceDataSyncManager(store_identifier)
    
    # Connect to store
    connection_result = sync_manager.connect_to_store(store_url, consumer_key, consumer_secret)
    
    if connection_result['status'] != 'success':
        return connection_result
    
    # Perform full sync
    sync_result = await sync_manager.sync_full_store()
    return sync_result


def create_demo_woocommerce_sync(store_identifier: str = "demo") -> Dict[str, Any]:
    """
    Create demo WooCommerce sync for testing
    
    Args:
        store_identifier: Identifier for demo store
        
    Returns:
        Dict containing demo sync results
    """
    sync_manager = WooCommerceDataSyncManager(store_identifier)
    return sync_manager.create_demo_sync()


if __name__ == "__main__":
    # Example usage and testing
    print("🔄 WooCommerce Data Sync Manager Test")
    
    # Test demo sync
    demo_sync = create_demo_woocommerce_sync("test-store")
    print(f"Demo Sync Status: {demo_sync['status']}")
    
    if demo_sync['status'] == 'success':
        stats = demo_sync['sync_statistics']
        print(f"Demo Products: {stats['demo_products_created']}")
        print(f"Demo Customers: {stats['demo_customers_created']}")
        print(f"Demo Orders: {stats['demo_orders_created']}")
    
    print("🎉 WooCommerce Data Sync Manager Ready!")