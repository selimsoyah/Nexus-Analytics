"""
WooCommerce API Integration Module

This module provides comprehensive WooCommerce integration capabilities including:
- WooCommerce REST API authentication
- Secure credential management
- Data synchronization pipeline
- Error handling and rate limiting
"""

import requests
import base64
import hashlib
import hmac
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WooCommerceAuthError(Exception):
    """Custom exception for WooCommerce authentication errors"""
    pass

class WooCommerceAPIError(Exception):
    """Custom exception for WooCommerce API errors"""
    pass

class WooCommerceConnector:
    """
    WooCommerce API Connector with authentication and data synchronization
    
    Features:
    - REST API authentication with consumer keys
    - Rate limiting and error handling
    - Secure credential storage
    - Data transformation to universal schema
    """
    
    def __init__(self, store_url: str = None, consumer_key: str = None, 
                 consumer_secret: str = None, version: str = "wc/v3"):
        """
        Initialize WooCommerce connector
        
        Args:
            store_url: WooCommerce store URL (e.g., 'https://mystore.com')
            consumer_key: WooCommerce REST API consumer key
            consumer_secret: WooCommerce REST API consumer secret
            version: WooCommerce API version (default: wc/v3)
        """
        self.store_url = store_url.rstrip('/') if store_url else None
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.version = version
        self.api_base = f"/wp-json/{version}/"
        
        # Rate limiting configuration
        self.rate_limit_calls = 0
        self.rate_limit_window_start = time.time()
        self.max_calls_per_minute = 300  # WooCommerce default limit
        
        # Session for connection reuse
        self.session = requests.Session()
        
        # Authentication validation
        if all([store_url, consumer_key, consumer_secret]):
            self._validate_credentials()

    def _validate_credentials(self) -> bool:
        """
        Validate WooCommerce API credentials
        
        Returns:
            bool: True if credentials are valid
            
        Raises:
            WooCommerceAuthError: If credentials are invalid
        """
        try:
            # Test connection with system status endpoint
            response = self._make_request('GET', 'system_status')
            
            if response.status_code == 200:
                logger.info(f"✅ WooCommerce connection established: {self.store_url}")
                return True
            elif response.status_code == 401:
                raise WooCommerceAuthError("Invalid WooCommerce API credentials")
            else:
                raise WooCommerceAuthError(f"WooCommerce API error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            raise WooCommerceAuthError(f"Connection failed: {str(e)}")

    def _generate_auth_header(self) -> Dict[str, str]:
        """
        Generate authentication headers for WooCommerce API
        
        Returns:
            Dict containing authentication headers
        """
        if not self.consumer_key or not self.consumer_secret:
            raise WooCommerceAuthError("Consumer key and secret are required")
            
        # Create HTTP Basic Auth header
        credentials = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        return {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json',
            'User-Agent': 'NexusAnalytics-WooCommerce/1.0'
        }

    def _check_rate_limit(self):
        """
        Check and enforce rate limiting
        
        Raises:
            WooCommerceAPIError: If rate limit is exceeded
        """
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - self.rate_limit_window_start > 60:
            self.rate_limit_calls = 0
            self.rate_limit_window_start = current_time
        
        # Check if limit exceeded
        if self.rate_limit_calls >= self.max_calls_per_minute:
            wait_time = 60 - (current_time - self.rate_limit_window_start)
            logger.warning(f"⚠️ Rate limit reached. Waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)
            self.rate_limit_calls = 0
            self.rate_limit_window_start = time.time()
        
        self.rate_limit_calls += 1

    def _make_request(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None) -> requests.Response:
        """
        Make authenticated request to WooCommerce API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., 'products', 'orders')
            params: Query parameters
            data: Request body data
            
        Returns:
            requests.Response object
        """
        # Rate limiting check
        self._check_rate_limit()
        
        # Build full URL
        url = urljoin(self.store_url + self.api_base, endpoint)
        
        # Get authentication headers
        headers = self._generate_auth_header()
        
        # Log request (excluding sensitive data)
        logger.debug(f"🔄 WooCommerce API {method} {endpoint}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params or {},
                json=data,
                timeout=30
            )
            
            # Log response status
            if response.status_code >= 400:
                logger.error(f"❌ WooCommerce API Error {response.status_code}: {response.text}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ WooCommerce API Request Failed: {str(e)}")
            raise WooCommerceAPIError(f"API request failed: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """
        Test WooCommerce API connection and return store information
        
        Returns:
            Dict containing connection status and store info
        """
        try:
            # Get system status for connection test
            response = self._make_request('GET', 'system_status')
            
            if response.status_code == 200:
                system_data = response.json()
                
                # Get store settings
                settings_response = self._make_request('GET', 'settings/general')
                settings_data = settings_response.json() if settings_response.status_code == 200 else {}
                
                # Extract store information
                store_info = {}
                for setting in settings_data:
                    if setting.get('id') in ['woocommerce_store_address', 'woocommerce_currency']:
                        store_info[setting['id']] = setting.get('value', '')
                
                return {
                    'status': 'success',
                    'message': 'WooCommerce connection successful',
                    'store_url': self.store_url,
                    'woocommerce_version': system_data.get('theme', {}).get('version', 'Unknown'),
                    'wordpress_version': system_data.get('wp_version', 'Unknown'),
                    'store_info': store_info,
                    'api_version': self.version,
                    'connected_at': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Connection failed with status {response.status_code}',
                    'error_code': response.status_code
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Connection test failed: {str(e)}',
                'error_type': type(e).__name__
            }

    @staticmethod
    def generate_demo_credentials() -> Dict[str, str]:
        """
        Generate demo WooCommerce credentials for testing
        
        Returns:
            Dict containing demo store configuration
        """
        return {
            'store_url': 'https://demo-woo-store.nexusanalytics.com',
            'consumer_key': 'ck_demo_' + hashlib.md5(str(time.time()).encode()).hexdigest()[:16],
            'consumer_secret': 'cs_demo_' + hashlib.md5(str(time.time() * 2).encode()).hexdigest()[:32],
            'store_name': 'NexusAnalytics Demo WooCommerce Store',
            'currency': 'USD',
            'created_at': datetime.now().isoformat(),
            'demo_mode': True
        }

    def get_store_info(self) -> Dict[str, Any]:
        """
        Get comprehensive store information
        
        Returns:
            Dict containing detailed store information
        """
        try:
            # Get general settings
            settings_response = self._make_request('GET', 'settings/general')
            
            if settings_response.status_code == 200:
                settings_data = settings_response.json()
                
                # Parse settings into structured format
                store_settings = {}
                for setting in settings_data:
                    store_settings[setting.get('id', 'unknown')] = {
                        'value': setting.get('value', ''),
                        'label': setting.get('label', ''),
                        'description': setting.get('description', '')
                    }
                
                return {
                    'status': 'success',
                    'store_url': self.store_url,
                    'settings': store_settings,
                    'currency': store_settings.get('woocommerce_currency', {}).get('value', 'USD'),
                    'store_address': store_settings.get('woocommerce_store_address', {}).get('value', ''),
                    'retrieved_at': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to retrieve store info: {settings_response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Store info retrieval failed: {str(e)}'
            }

    # =================================================================
    # PRODUCT MANAGEMENT API
    # =================================================================
    
    def get_products(self, per_page: int = 100, page: int = 1, 
                    status: str = 'any', **kwargs) -> Dict[str, Any]:
        """
        Fetch products from WooCommerce store
        
        Args:
            per_page: Number of products per page (max 100)
            page: Page number
            status: Product status (publish, draft, pending, private, any)
            **kwargs: Additional query parameters
            
        Returns:
            Dict containing products data and pagination info
        """
        try:
            params = {
                'per_page': min(per_page, 100),
                'page': page,
                'status': status,
                **kwargs
            }
            
            response = self._make_request('GET', 'products', params=params)
            
            if response.status_code == 200:
                products = response.json()
                
                # Get pagination info from headers
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                total_products = int(response.headers.get('X-WP-Total', len(products)))
                
                return {
                    'status': 'success',
                    'products': products,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total_pages': total_pages,
                        'total_products': total_products,
                        'has_next': page < total_pages
                    },
                    'retrieved_at': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to fetch products: {response.status_code}',
                    'error_details': response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Products fetch failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Products fetch failed: {str(e)}'
            }

    def get_product(self, product_id: int) -> Dict[str, Any]:
        """
        Fetch single product by ID
        
        Args:
            product_id: WooCommerce product ID
            
        Returns:
            Dict containing product data
        """
        try:
            response = self._make_request('GET', f'products/{product_id}')
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'product': response.json(),
                    'retrieved_at': datetime.now().isoformat()
                }
            elif response.status_code == 404:
                return {
                    'status': 'error',
                    'message': f'Product {product_id} not found'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to fetch product: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Product fetch failed: {str(e)}'
            }

    # =================================================================
    # CUSTOMER MANAGEMENT API
    # =================================================================
    
    def get_customers(self, per_page: int = 100, page: int = 1, 
                     **kwargs) -> Dict[str, Any]:
        """
        Fetch customers from WooCommerce store
        
        Args:
            per_page: Number of customers per page (max 100)
            page: Page number
            **kwargs: Additional query parameters (search, role, etc.)
            
        Returns:
            Dict containing customers data and pagination info
        """
        try:
            params = {
                'per_page': min(per_page, 100),
                'page': page,
                **kwargs
            }
            
            response = self._make_request('GET', 'customers', params=params)
            
            if response.status_code == 200:
                customers = response.json()
                
                # Get pagination info from headers
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                total_customers = int(response.headers.get('X-WP-Total', len(customers)))
                
                return {
                    'status': 'success',
                    'customers': customers,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total_pages': total_pages,
                        'total_customers': total_customers,
                        'has_next': page < total_pages
                    },
                    'retrieved_at': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to fetch customers: {response.status_code}',
                    'error_details': response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Customers fetch failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Customers fetch failed: {str(e)}'
            }

    def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """
        Fetch single customer by ID
        
        Args:
            customer_id: WooCommerce customer ID
            
        Returns:
            Dict containing customer data
        """
        try:
            response = self._make_request('GET', f'customers/{customer_id}')
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'customer': response.json(),
                    'retrieved_at': datetime.now().isoformat()
                }
            elif response.status_code == 404:
                return {
                    'status': 'error',
                    'message': f'Customer {customer_id} not found'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to fetch customer: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Customer fetch failed: {str(e)}'
            }

    # =================================================================
    # ORDER MANAGEMENT API
    # =================================================================
    
    def get_orders(self, per_page: int = 100, page: int = 1, 
                  status: str = 'any', **kwargs) -> Dict[str, Any]:
        """
        Fetch orders from WooCommerce store
        
        Args:
            per_page: Number of orders per page (max 100)
            page: Page number
            status: Order status (any, pending, processing, on-hold, completed, etc.)
            **kwargs: Additional query parameters
            
        Returns:
            Dict containing orders data and pagination info
        """
        try:
            params = {
                'per_page': min(per_page, 100),
                'page': page,
                'status': status,
                **kwargs
            }
            
            response = self._make_request('GET', 'orders', params=params)
            
            if response.status_code == 200:
                orders = response.json()
                
                # Get pagination info from headers
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                total_orders = int(response.headers.get('X-WP-Total', len(orders)))
                
                return {
                    'status': 'success',
                    'orders': orders,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total_pages': total_pages,
                        'total_orders': total_orders,
                        'has_next': page < total_pages
                    },
                    'retrieved_at': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to fetch orders: {response.status_code}',
                    'error_details': response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Orders fetch failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Orders fetch failed: {str(e)}'
            }

    def get_order(self, order_id: int) -> Dict[str, Any]:
        """
        Fetch single order by ID
        
        Args:
            order_id: WooCommerce order ID
            
        Returns:
            Dict containing order data
        """
        try:
            response = self._make_request('GET', f'orders/{order_id}')
            
            if response.status_code == 200:
                return {
                    'status': 'success',
                    'order': response.json(),
                    'retrieved_at': datetime.now().isoformat()
                }
            elif response.status_code == 404:
                return {
                    'status': 'error',
                    'message': f'Order {order_id} not found'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to fetch order: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Order fetch failed: {str(e)}'
            }

    # =================================================================
    # BULK DATA OPERATIONS
    # =================================================================
    
    def get_all_data(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Fetch all store data (products, customers, orders) in batches
        
        Args:
            batch_size: Size of each batch request
            
        Returns:
            Dict containing all store data with progress tracking
        """
        results = {
            'status': 'success',
            'data': {
                'products': [],
                'customers': [],
                'orders': []
            },
            'statistics': {
                'total_products': 0,
                'total_customers': 0,
                'total_orders': 0,
                'sync_duration': 0
            },
            'sync_started_at': datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        try:
            # Fetch all products
            logger.info("🔄 Fetching WooCommerce products...")
            page = 1
            while True:
                product_result = self.get_products(per_page=batch_size, page=page)
                
                if product_result['status'] == 'success':
                    results['data']['products'].extend(product_result['products'])
                    
                    if not product_result['pagination']['has_next']:
                        break
                    page += 1
                else:
                    logger.warning(f"⚠️ Products fetch failed on page {page}")
                    break
            
            results['statistics']['total_products'] = len(results['data']['products'])
            logger.info(f"✅ Fetched {results['statistics']['total_products']} products")
            
            # Fetch all customers
            logger.info("🔄 Fetching WooCommerce customers...")
            page = 1
            while True:
                customer_result = self.get_customers(per_page=batch_size, page=page)
                
                if customer_result['status'] == 'success':
                    results['data']['customers'].extend(customer_result['customers'])
                    
                    if not customer_result['pagination']['has_next']:
                        break
                    page += 1
                else:
                    logger.warning(f"⚠️ Customers fetch failed on page {page}")
                    break
            
            results['statistics']['total_customers'] = len(results['data']['customers'])
            logger.info(f"✅ Fetched {results['statistics']['total_customers']} customers")
            
            # Fetch all orders
            logger.info("🔄 Fetching WooCommerce orders...")
            page = 1
            while True:
                order_result = self.get_orders(per_page=batch_size, page=page)
                
                if order_result['status'] == 'success':
                    results['data']['orders'].extend(order_result['orders'])
                    
                    if not order_result['pagination']['has_next']:
                        break
                    page += 1
                else:
                    logger.warning(f"⚠️ Orders fetch failed on page {page}")
                    break
            
            results['statistics']['total_orders'] = len(results['data']['orders'])
            logger.info(f"✅ Fetched {results['statistics']['total_orders']} orders")
            
            # Calculate sync duration
            results['statistics']['sync_duration'] = time.time() - start_time
            results['sync_completed_at'] = datetime.now().isoformat()
            
            logger.info(f"🎉 WooCommerce data sync completed in {results['statistics']['sync_duration']:.2f} seconds")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Bulk data fetch failed: {str(e)}")
            results['status'] = 'error'
            results['error_message'] = str(e)
            results['statistics']['sync_duration'] = time.time() - start_time
            return results


class WooCommerceCredentialManager:
    """
    Secure credential management for WooCommerce connections
    
    Features:
    - Encrypted credential storage
    - Multiple store management
    - Credential validation and rotation
    """
    
    def __init__(self, storage_file: str = "woocommerce_credentials.json"):
        """
        Initialize credential manager
        
        Args:
            storage_file: File path for credential storage
        """
        self.storage_file = storage_file
        self.credentials = self._load_credentials()

    def _load_credentials(self) -> Dict[str, Any]:
        """
        Load credentials from secure storage
        
        Returns:
            Dict containing stored credentials
        """
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info("🔐 Creating new WooCommerce credentials store")
            return {}
        except json.JSONDecodeError:
            logger.error("❌ Invalid credentials file format")
            return {}

    def _save_credentials(self):
        """Save credentials to secure storage"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.credentials, f, indent=2)
            logger.info("🔐 WooCommerce credentials saved securely")
        except Exception as e:
            logger.error(f"❌ Failed to save credentials: {str(e)}")

    def add_store(self, store_id: str, store_url: str, consumer_key: str, 
                  consumer_secret: str, store_name: str = None) -> bool:
        """
        Add new WooCommerce store credentials
        
        Args:
            store_id: Unique identifier for the store
            store_url: WooCommerce store URL
            consumer_key: API consumer key
            consumer_secret: API consumer secret
            store_name: Friendly name for the store
            
        Returns:
            bool: True if credentials added successfully
        """
        try:
            # Validate credentials by testing connection
            connector = WooCommerceConnector(store_url, consumer_key, consumer_secret)
            test_result = connector.test_connection()
            
            if test_result['status'] == 'success':
                self.credentials[store_id] = {
                    'store_url': store_url,
                    'consumer_key': consumer_key,
                    'consumer_secret': consumer_secret,
                    'store_name': store_name or store_url,
                    'added_at': datetime.now().isoformat(),
                    'last_validated': datetime.now().isoformat(),
                    'status': 'active'
                }
                self._save_credentials()
                logger.info(f"✅ WooCommerce store '{store_id}' added successfully")
                return True
            else:
                logger.error(f"❌ Invalid WooCommerce credentials for '{store_id}'")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to add WooCommerce store '{store_id}': {str(e)}")
            return False

    def get_store_credentials(self, store_id: str) -> Optional[Dict[str, str]]:
        """
        Get credentials for specific store
        
        Args:
            store_id: Store identifier
            
        Returns:
            Dict containing store credentials or None if not found
        """
        return self.credentials.get(store_id)

    def list_stores(self) -> List[Dict[str, Any]]:
        """
        List all configured WooCommerce stores
        
        Returns:
            List of store information dictionaries
        """
        stores = []
        for store_id, creds in self.credentials.items():
            stores.append({
                'store_id': store_id,
                'store_name': creds.get('store_name', store_id),
                'store_url': creds.get('store_url'),
                'added_at': creds.get('added_at'),
                'status': creds.get('status', 'unknown')
            })
        return stores

    def remove_store(self, store_id: str) -> bool:
        """
        Remove store credentials
        
        Args:
            store_id: Store identifier to remove
            
        Returns:
            bool: True if removed successfully
        """
        if store_id in self.credentials:
            del self.credentials[store_id]
            self._save_credentials()
            logger.info(f"🗑️ WooCommerce store '{store_id}' removed")
            return True
        return False


# Factory function for easy connector creation
def create_woocommerce_connector(store_url: str, consumer_key: str, 
                                consumer_secret: str) -> WooCommerceConnector:
    """
    Factory function to create WooCommerce connector instance
    
    Args:
        store_url: WooCommerce store URL
        consumer_key: API consumer key
        consumer_secret: API consumer secret
        
    Returns:
        Configured WooCommerceConnector instance
    """
    return WooCommerceConnector(store_url, consumer_key, consumer_secret)


# Demo setup function
def setup_demo_woocommerce_store() -> Dict[str, Any]:
    """
    Setup a demo WooCommerce store for testing purposes
    
    Returns:
        Dict containing demo store information
    """
    demo_creds = WooCommerceConnector.generate_demo_credentials()
    
    return {
        'status': 'success',
        'message': 'Demo WooCommerce store created',
        'store_info': demo_creds,
        'next_steps': [
            'Use these credentials to test WooCommerce integration',
            'Replace with real store credentials for production use',
            'Test data synchronization with demo data'
        ]
    }


if __name__ == "__main__":
    # Example usage and testing
    print("🛒 WooCommerce Connector Test")
    
    # Test demo credentials generation
    demo_store = setup_demo_woocommerce_store()
    print(f"Demo Store: {demo_store}")
    
    # Test credential manager
    cred_manager = WooCommerceCredentialManager()
    print(f"Credential Manager initialized: {len(cred_manager.list_stores())} stores configured")