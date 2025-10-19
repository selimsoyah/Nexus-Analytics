"""
WooCommerce Universal Schema Mapper

This module transforms WooCommerce API data into the universal schema format
used across all platforms in the Nexus Analytics system.

Universal Schema Structure:
- Orders: Standardized order format across all platforms
- Customers: Unified customer profile structure  
- Products: Common product data format
- Line Items: Standardized order line items
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WooCommerceSchemaMapper:
    """
    Maps WooCommerce API responses to universal schema format
    
    Handles transformation of:
    - Orders from WooCommerce to universal order format
    - Customers from WooCommerce to universal customer format
    - Products from WooCommerce to universal product format
    """
    
    def __init__(self, store_identifier: str = "woocommerce"):
        """
        Initialize schema mapper
        
        Args:
            store_identifier: Unique identifier for this WooCommerce store
        """
        self.platform = "woocommerce"
        self.store_identifier = store_identifier

    # =================================================================
    # ORDER MAPPING
    # =================================================================
    
    def map_order_to_universal(self, woo_order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform WooCommerce order to universal schema
        
        Args:
            woo_order: Raw WooCommerce order data
            
        Returns:
            Dict in universal order schema format
        """
        try:
            # Extract billing and shipping addresses
            billing = woo_order.get('billing', {})
            shipping = woo_order.get('shipping', {})
            
            # Calculate totals
            line_items = woo_order.get('line_items', [])
            total_quantity = sum(item.get('quantity', 0) for item in line_items)
            
            # Map order status
            status_mapping = {
                'pending': 'pending',
                'processing': 'processing', 
                'on-hold': 'on_hold',
                'completed': 'completed',
                'cancelled': 'cancelled',
                'refunded': 'refunded',
                'failed': 'failed'
            }
            
            universal_order = {
                # Core identifiers
                'order_id': str(woo_order.get('id')),
                'platform_order_id': str(woo_order.get('id')),
                'platform': self.platform,
                'store_identifier': self.store_identifier,
                
                # Customer information
                'customer_id': str(woo_order.get('customer_id', 0)),
                'customer_external_id': str(woo_order.get('customer_id', 0)) if woo_order.get('customer_id') else None,
                'customer_email': billing.get('email', ''),
                'customer_phone': billing.get('phone', ''),
                
                # Order details
                'order_number': woo_order.get('number', str(woo_order.get('id'))),
                'order_date': self._parse_woo_date(woo_order.get('date_created')),
                'order_status': status_mapping.get(woo_order.get('status'), 'unknown'),
                'currency': woo_order.get('currency', 'USD'),
                
                # Financial information
                'total_amount': float(woo_order.get('total', 0)),
                'subtotal': float(woo_order.get('line_items_total', 0)),
                'tax_amount': float(woo_order.get('total_tax', 0)),
                'shipping_amount': float(woo_order.get('shipping_total', 0)),
                'discount_amount': float(woo_order.get('discount_total', 0)),
                'total_quantity': total_quantity,
                
                # Addresses
                'billing_address': self._map_woo_address(billing),
                'shipping_address': self._map_woo_address(shipping),
                
                # Line items
                'line_items': [self.map_line_item_to_universal(item) for item in line_items],
                
                # Metadata
                'payment_method': woo_order.get('payment_method_title', ''),
                'notes': woo_order.get('customer_note', ''),
                'meta_data': self._extract_woo_metadata(woo_order.get('meta_data', [])),
                
                # Timestamps
                'created_at': self._parse_woo_date(woo_order.get('date_created')),
                'updated_at': self._parse_woo_date(woo_order.get('date_modified')),
                'completed_at': self._parse_woo_date(woo_order.get('date_completed')),
                
                # Platform-specific data
                'platform_data': {
                    'woo_order_key': woo_order.get('order_key'),
                    'woo_status': woo_order.get('status'),
                    'woo_parent_id': woo_order.get('parent_id'),
                    'woo_version': woo_order.get('version')
                }
            }
            
            return universal_order
            
        except Exception as e:
            logger.error(f"❌ WooCommerce order mapping failed: {str(e)}")
            return {
                'error': f'Order mapping failed: {str(e)}',
                'raw_order': woo_order
            }

    def map_line_item_to_universal(self, woo_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform WooCommerce line item to universal schema
        
        Args:
            woo_item: Raw WooCommerce line item data
            
        Returns:
            Dict in universal line item schema format
        """
        try:
            return {
                'line_item_id': str(woo_item.get('id')),
                'product_id': str(woo_item.get('product_id')),
                'product_name': woo_item.get('name', ''),
                'product_sku': woo_item.get('sku', ''),
                'variant_id': str(woo_item.get('variation_id')) if woo_item.get('variation_id') else None,
                'quantity': int(woo_item.get('quantity', 1)),
                'unit_price': float(woo_item.get('price', 0)),
                'total_price': float(woo_item.get('total', 0)),
                'tax_amount': float(woo_item.get('total_tax', 0)),
                'platform_data': {
                    'woo_subtotal': woo_item.get('subtotal'),
                    'woo_subtotal_tax': woo_item.get('subtotal_tax'),
                    'woo_meta_data': woo_item.get('meta_data', [])
                }
            }
        except Exception as e:
            logger.error(f"❌ Line item mapping failed: {str(e)}")
            return {'error': f'Line item mapping failed: {str(e)}'}

    # =================================================================
    # CUSTOMER MAPPING
    # =================================================================
    
    def map_customer_to_universal(self, woo_customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform WooCommerce customer to universal schema
        
        Args:
            woo_customer: Raw WooCommerce customer data
            
        Returns:
            Dict in universal customer schema format
        """
        try:
            billing = woo_customer.get('billing', {})
            shipping = woo_customer.get('shipping', {})
            
            universal_customer = {
                # Core identifiers
                'customer_id': str(woo_customer.get('id')),
                'customer_external_id': str(woo_customer.get('id')),
                'platform': self.platform,
                'store_identifier': self.store_identifier,
                
                # Personal information
                'first_name': woo_customer.get('first_name', ''),
                'last_name': woo_customer.get('last_name', ''),
                'email': woo_customer.get('email', ''),
                'phone': billing.get('phone', ''),
                'username': woo_customer.get('username', ''),
                
                # Account information
                'date_registered': self._parse_woo_date(woo_customer.get('date_created')),
                'last_login': self._parse_woo_date(woo_customer.get('date_modified')),
                'is_active': True,  # WooCommerce doesn't have inactive customers
                'customer_group': woo_customer.get('role', 'customer'),
                
                # Statistics
                'total_orders': woo_customer.get('orders_count', 0),
                'total_spent': float(woo_customer.get('total_spent', 0)),
                'avatar_url': woo_customer.get('avatar_url', ''),
                
                # Addresses
                'billing_address': self._map_woo_address(billing),
                'shipping_address': self._map_woo_address(shipping),
                
                # Metadata
                'meta_data': self._extract_woo_metadata(woo_customer.get('meta_data', [])),
                
                # Timestamps
                'created_at': self._parse_woo_date(woo_customer.get('date_created')),
                'updated_at': self._parse_woo_date(woo_customer.get('date_modified')),
                
                # Platform-specific data
                'platform_data': {
                    'woo_role': woo_customer.get('role'),
                    'woo_is_paying_customer': woo_customer.get('is_paying_customer', False),
                    'woo_date_created_gmt': woo_customer.get('date_created_gmt'),
                    'woo_date_modified_gmt': woo_customer.get('date_modified_gmt')
                }
            }
            
            return universal_customer
            
        except Exception as e:
            logger.error(f"❌ WooCommerce customer mapping failed: {str(e)}")
            return {
                'error': f'Customer mapping failed: {str(e)}',
                'raw_customer': woo_customer
            }

    # =================================================================
    # PRODUCT MAPPING
    # =================================================================
    
    def map_product_to_universal(self, woo_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform WooCommerce product to universal schema
        
        Args:
            woo_product: Raw WooCommerce product data
            
        Returns:
            Dict in universal product schema format
        """
        try:
            # Map product type
            type_mapping = {
                'simple': 'simple',
                'grouped': 'bundle',
                'external': 'external',
                'variable': 'variable'
            }
            
            # Map product status
            status_mapping = {
                'publish': 'active',
                'draft': 'draft',
                'pending': 'pending',
                'private': 'private'
            }
            
            universal_product = {
                # Core identifiers
                'product_id': str(woo_product.get('id')),
                'platform_product_id': str(woo_product.get('id')),
                'platform': self.platform,
                'store_identifier': self.store_identifier,
                
                # Basic information
                'name': woo_product.get('name', ''),
                'slug': woo_product.get('slug', ''),
                'description': woo_product.get('description', ''),
                'short_description': woo_product.get('short_description', ''),
                'sku': woo_product.get('sku', ''),
                
                # Product classification
                'type': type_mapping.get(woo_product.get('type'), 'simple'),
                'status': status_mapping.get(woo_product.get('status'), 'unknown'),
                'featured': woo_product.get('featured', False),
                'virtual': woo_product.get('virtual', False),
                'downloadable': woo_product.get('downloadable', False),
                
                # Pricing
                'price': float(woo_product.get('price', 0)),
                'regular_price': float(woo_product.get('regular_price', 0)),
                'sale_price': float(woo_product.get('sale_price', 0)) if woo_product.get('sale_price') else None,
                'on_sale': woo_product.get('on_sale', False),
                
                # Inventory
                'manage_stock': woo_product.get('manage_stock', False),
                'stock_quantity': woo_product.get('stock_quantity'),
                'stock_status': woo_product.get('stock_status', 'instock'),
                'backorders': woo_product.get('backorders', 'no'),
                'low_stock_amount': woo_product.get('low_stock_amount'),
                
                # Physical properties
                'weight': woo_product.get('weight'),
                'dimensions': {
                    'length': woo_product.get('dimensions', {}).get('length'),
                    'width': woo_product.get('dimensions', {}).get('width'), 
                    'height': woo_product.get('dimensions', {}).get('height')
                },
                'shipping_required': woo_product.get('shipping_required', True),
                'shipping_taxable': woo_product.get('shipping_taxable', True),
                
                # Categories and tags
                'categories': [cat.get('name') for cat in woo_product.get('categories', [])],
                'tags': [tag.get('name') for tag in woo_product.get('tags', [])],
                
                # Images
                'images': [img.get('src') for img in woo_product.get('images', [])],
                'featured_image': woo_product.get('images', [{}])[0].get('src') if woo_product.get('images') else None,
                
                # SEO and external
                'permalink': woo_product.get('permalink', ''),
                'external_url': woo_product.get('external_url', ''),
                'button_text': woo_product.get('button_text', ''),
                
                # Reviews and ratings
                'rating_count': woo_product.get('rating_count', 0),
                'average_rating': float(woo_product.get('average_rating', 0)),
                'reviews_allowed': woo_product.get('reviews_allowed', True),
                
                # Timestamps
                'created_at': self._parse_woo_date(woo_product.get('date_created')),
                'updated_at': self._parse_woo_date(woo_product.get('date_modified')),
                
                # Platform-specific data
                'platform_data': {
                    'woo_type': woo_product.get('type'),
                    'woo_status': woo_product.get('status'),
                    'woo_catalog_visibility': woo_product.get('catalog_visibility'),
                    'woo_total_sales': woo_product.get('total_sales', 0),
                    'woo_tax_status': woo_product.get('tax_status'),
                    'woo_tax_class': woo_product.get('tax_class'),
                    'woo_parent_id': woo_product.get('parent_id'),
                    'woo_menu_order': woo_product.get('menu_order')
                }
            }
            
            return universal_product
            
        except Exception as e:
            logger.error(f"❌ WooCommerce product mapping failed: {str(e)}")
            return {
                'error': f'Product mapping failed: {str(e)}',
                'raw_product': woo_product
            }

    # =================================================================
    # UTILITY METHODS
    # =================================================================
    
    def _parse_woo_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parse WooCommerce date string to ISO format
        
        Args:
            date_str: WooCommerce date string
            
        Returns:
            ISO formatted date string or None
        """
        if not date_str:
            return None
            
        try:
            # WooCommerce typically returns dates in ISO format already
            # But we'll ensure consistency
            if 'T' in date_str:
                return date_str  # Already in ISO format
            else:
                # Handle other date formats if needed
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.isoformat()
        except Exception:
            return date_str  # Return original if parsing fails

    def _map_woo_address(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map WooCommerce address to universal address format
        
        Args:
            address_data: WooCommerce address data
            
        Returns:
            Universal address format
        """
        return {
            'first_name': address_data.get('first_name', ''),
            'last_name': address_data.get('last_name', ''),
            'company': address_data.get('company', ''),
            'address_line_1': address_data.get('address_1', ''),
            'address_line_2': address_data.get('address_2', ''),
            'city': address_data.get('city', ''),
            'state': address_data.get('state', ''),
            'postal_code': address_data.get('postcode', ''),
            'country': address_data.get('country', ''),
            'email': address_data.get('email', ''),
            'phone': address_data.get('phone', '')
        }

    def _extract_woo_metadata(self, meta_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract and flatten WooCommerce metadata
        
        Args:
            meta_data: List of WooCommerce meta data objects
            
        Returns:
            Flattened metadata dictionary
        """
        metadata = {}
        
        for item in meta_data:
            key = item.get('key', '')
            value = item.get('value', '')
            
            # Skip internal WooCommerce keys (starting with _)
            if not key.startswith('_'):
                metadata[key] = value
                
        return metadata

    # =================================================================
    # BATCH MAPPING OPERATIONS
    # =================================================================
    
    def map_batch_orders(self, woo_orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map multiple WooCommerce orders to universal schema
        
        Args:
            woo_orders: List of WooCommerce order objects
            
        Returns:
            List of orders in universal schema format
        """
        return [self.map_order_to_universal(order) for order in woo_orders]

    def map_batch_customers(self, woo_customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map multiple WooCommerce customers to universal schema
        
        Args:
            woo_customers: List of WooCommerce customer objects
            
        Returns:
            List of customers in universal schema format
        """
        return [self.map_customer_to_universal(customer) for customer in woo_customers]

    def map_batch_products(self, woo_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map multiple WooCommerce products to universal schema
        
        Args:
            woo_products: List of WooCommerce product objects
            
        Returns:
            List of products in universal schema format
        """
        return [self.map_product_to_universal(product) for product in woo_products]

    def get_mapping_statistics(self, mapped_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistics about mapping operation
        
        Args:
            mapped_data: List of mapped objects
            
        Returns:
            Dictionary containing mapping statistics
        """
        total_items = len(mapped_data)
        successful_mappings = len([item for item in mapped_data if 'error' not in item])
        failed_mappings = total_items - successful_mappings
        
        return {
            'total_items': total_items,
            'successful_mappings': successful_mappings,
            'failed_mappings': failed_mappings,
            'success_rate': (successful_mappings / total_items * 100) if total_items > 0 else 0,
            'mapping_completed_at': datetime.now().isoformat()
        }


# Convenience functions for direct usage
def map_woocommerce_order(woo_order: Dict[str, Any], store_identifier: str = "default") -> Dict[str, Any]:
    """Map single WooCommerce order to universal schema"""
    mapper = WooCommerceSchemaMapper(store_identifier)
    return mapper.map_order_to_universal(woo_order)

def map_woocommerce_customer(woo_customer: Dict[str, Any], store_identifier: str = "default") -> Dict[str, Any]:
    """Map single WooCommerce customer to universal schema"""
    mapper = WooCommerceSchemaMapper(store_identifier)
    return mapper.map_customer_to_universal(woo_customer)

def map_woocommerce_product(woo_product: Dict[str, Any], store_identifier: str = "default") -> Dict[str, Any]:
    """Map single WooCommerce product to universal schema"""
    mapper = WooCommerceSchemaMapper(store_identifier)
    return mapper.map_product_to_universal(woo_product)


if __name__ == "__main__":
    # Example usage and testing
    print("🗂️ WooCommerce Schema Mapper Test")
    
    # Test order mapping
    sample_woo_order = {
        'id': 12345,
        'number': 'ORD-001',
        'status': 'completed',
        'currency': 'USD',
        'total': '99.99',
        'date_created': '2023-10-19T10:30:00',
        'customer_id': 67890,
        'billing': {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com'
        },
        'line_items': [{
            'id': 1,
            'product_id': 111,
            'name': 'Test Product',
            'quantity': 2,
            'total': '99.99'
        }]
    }
    
    mapper = WooCommerceSchemaMapper("test-store")
    universal_order = mapper.map_order_to_universal(sample_woo_order)
    
    print(f"✅ Mapped order {universal_order.get('order_id')} to universal schema")
    print(f"   Platform: {universal_order.get('platform')}")
    print(f"   Total: {universal_order.get('currency')} {universal_order.get('total_amount')}")