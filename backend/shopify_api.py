"""
Shopify Integration API Endpoints
Real-world e-commerce platform integration for Nexus Analytics
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from shopify_connector import ShopifyConnector
from auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()
shopify = ShopifyConnector()

@router.get("/shopify/oauth-url")
def get_shopify_oauth_url(
    shop_domain: str = Query(..., description="Shopify store domain (without .myshopify.com)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate Shopify OAuth authorization URL for store connection
    
    Args:
        shop_domain: The shop's domain name (e.g., 'my-store' for my-store.myshopify.com)
        
    Returns:
        Authorization URL for user to approve app installation
    """
    try:
        # Validate shop domain format
        if not shop_domain or '.' in shop_domain:
            raise HTTPException(
                status_code=400, 
                detail="Shop domain should be just the store name (without .myshopify.com)"
            )
        
        oauth_data = shopify.get_oauth_url(shop_domain)
        
        return {
            "success": True,
            "message": "OAuth URL generated successfully",
            "data": oauth_data,
            "instructions": [
                "1. Visit the authorization_url in your browser",
                "2. Log into your Shopify store as an admin",
                "3. Review and approve the requested permissions",
                "4. You'll be redirected back with an authorization code",
                "5. Use the /shopify/connect endpoint with the code"
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"OAuth URL generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate OAuth URL: {str(e)}")

@router.post("/shopify/connect")  
def connect_shopify_store(
    request_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Complete Shopify store connection using OAuth authorization code
    
    Expected request body:
    {
        "shop_domain": "my-store",
        "code": "authorization_code_from_callback",
        "state": "state_parameter_from_oauth"
    }
    
    Returns:
        Connection status and shop information
    """
    try:
        shop_domain = request_data.get('shop_domain')
        code = request_data.get('code')
        
        if not shop_domain or not code:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: shop_domain and code"
            )
        
        # Exchange code for access token
        token_result = shopify.exchange_code_for_token(shop_domain, code)
        
        if not token_result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=token_result.get('error', 'Token exchange failed')
            )
        
        # Get shop information to verify connection
        shop_info = shopify.get_shop_info(shop_domain)
        
        return {
            "success": True,
            "message": f"Successfully connected to {shop_domain}.myshopify.com",
            "data": {
                "shop_domain": shop_domain,
                "connection_status": "active",
                "shop_info": shop_info.get('shop_info', {}),
                "available_data": {
                    "customers": "Ready to sync",
                    "orders": "Ready to sync", 
                    "products": "Ready to sync"
                },
                "next_steps": [
                    "Use /shopify/sync-customers to import customer data",
                    "Use /shopify/sync-orders to import order data",
                    "Use /shopify/sync-products to import product data"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Shopify connection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

@router.post("/shopify/sync-customers")
def sync_shopify_customers(
    shop_domain: str = Query(..., description="Shop domain to sync from"),
    limit: int = Query(50, description="Maximum customers to sync", ge=1, le=250),
    current_user: dict = Depends(get_current_user)
):
    """
    Sync customers from Shopify store to Nexus Analytics
    
    Args:
        shop_domain: Shopify store domain
        limit: Maximum number of customers to sync (1-250)
        
    Returns:
        Sync results with customer count and status
    """
    try:
        result = shopify.sync_customers(shop_domain, limit)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Customer sync failed')
            )
        
        return {
            "success": True,
            "message": "Customer sync completed successfully",
            "data": {
                "customers_synced": result['customers_synced'],
                "total_available": result['total_available'],
                "errors": result.get('errors', []),
                "shop_domain": shop_domain,
                "sync_timestamp": datetime.now().isoformat()
            },
            "recommendations": [
                "Run analytics/clv/trends to see customer lifetime value analysis",
                "Use analytics/segmentation/rfm for customer segmentation",
                "Check analytics/cross-platform-insights for unified reporting"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Customer sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Customer sync failed: {str(e)}")

@router.post("/shopify/sync-orders")
def sync_shopify_orders(
    shop_domain: str = Query(..., description="Shop domain to sync from"),
    limit: int = Query(50, description="Maximum orders to sync", ge=1, le=250),
    status: str = Query("any", description="Order status filter"),
    current_user: dict = Depends(get_current_user)
):
    """
    Sync orders from Shopify store to Nexus Analytics
    
    Args:
        shop_domain: Shopify store domain  
        limit: Maximum number of orders to sync (1-250)
        status: Order status filter ('open', 'closed', 'cancelled', 'any')
        
    Returns:
        Sync results with order count and status
    """
    try:
        result = shopify.sync_orders(shop_domain, limit, status)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Order sync failed')
            )
        
        return {
            "success": True,
            "message": "Order sync completed successfully", 
            "data": {
                "orders_synced": result['orders_synced'],
                "total_available": result['total_available'],
                "errors": result.get('errors', []),
                "shop_domain": shop_domain,
                "status_filter": status,
                "sync_timestamp": datetime.now().isoformat()
            },
            "analytics_available": [
                "Revenue forecasting with real data",
                "Cross-platform order analysis", 
                "Customer purchase patterns",
                "Product performance metrics"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Order sync failed: {str(e)}")

@router.post("/shopify/sync-products")
def sync_shopify_products(
    shop_domain: str = Query(..., description="Shop domain to sync from"),
    limit: int = Query(50, description="Maximum products to sync", ge=1, le=250),
    current_user: dict = Depends(get_current_user)
):
    """
    Sync products from Shopify store to Nexus Analytics
    
    Args:
        shop_domain: Shopify store domain
        limit: Maximum number of products to sync (1-250)
        
    Returns:
        Sync results with product count and status
    """
    try:
        result = shopify.sync_products(shop_domain, limit)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Product sync failed')
            )
        
        return {
            "success": True,
            "message": "Product sync completed successfully",
            "data": {
                "products_synced": result['products_synced'],
                "total_available": result['total_available'],
                "errors": result.get('errors', []),
                "shop_domain": shop_domain,
                "sync_timestamp": datetime.now().isoformat()
            },
            "analytics_available": [
                "Product performance analysis",
                "Category-based insights",
                "Cross-platform product comparison",
                "Inventory and pricing analytics"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Product sync failed: {str(e)}")

@router.get("/shopify/connection-status")
def get_shopify_connection_status(
    shop_domain: Optional[str] = Query(None, description="Specific shop to check"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get status of Shopify connections
    
    Args:
        shop_domain: Optional specific shop to check, or all if not provided
        
    Returns:
        Connection status and shop information
    """
    try:
        if shop_domain:
            # Check specific shop
            shop_info = shopify.get_shop_info(shop_domain)
            
            return {
                "success": True,
                "data": {
                    "shop_domain": shop_domain,
                    "connection_status": "active" if shop_info.get('success') else "disconnected",
                    "shop_info": shop_info.get('shop_info', {}),
                    "error": shop_info.get('error') if not shop_info.get('success') else None
                }
            }
        else:
            # Get all connected shops from database
            from sqlalchemy import text
            from database import engine
            
            query = "SELECT shop_domain, created_at, last_sync, status FROM shopify_connections WHERE status = 'active'"
            
            with engine.connect() as conn:
                result = conn.execute(text(query))
                connections = [dict(row._mapping) for row in result]
            
            return {
                "success": True,
                "data": {
                    "total_connections": len(connections),
                    "active_shops": connections,
                    "message": "Use shop_domain parameter to check specific shop details"
                }
            }
        
    except Exception as e:
        logger.error(f"Connection status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/shopify/full-sync")
def full_shopify_sync(
    shop_domain: str = Query(..., description="Shop domain to sync"),
    customers_limit: int = Query(100, description="Max customers to sync"),
    orders_limit: int = Query(100, description="Max orders to sync"),
    products_limit: int = Query(50, description="Max products to sync"),
    current_user: dict = Depends(get_current_user)
):
    """
    Perform complete data synchronization from Shopify store
    
    Syncs customers, orders, and products in sequence with progress tracking
    
    Args:
        shop_domain: Shopify store domain
        customers_limit: Maximum customers to sync
        orders_limit: Maximum orders to sync  
        products_limit: Maximum products to sync
        
    Returns:
        Complete sync results for all data types
    """
    try:
        sync_results = {
            "shop_domain": shop_domain,
            "sync_started_at": datetime.now().isoformat(),
            "results": {},
            "errors": [],
            "warnings": []
        }
        
        # 1. Sync customers first (needed for order relationships)
        try:
            customer_result = shopify.sync_customers(shop_domain, customers_limit)
            sync_results["results"]["customers"] = customer_result
            if customer_result.get('errors'):
                sync_results["warnings"].extend([f"Customer: {err}" for err in customer_result['errors']])
        except Exception as e:
            sync_results["errors"].append(f"Customer sync failed: {str(e)}")
        
        # 2. Sync products (needed for order item relationships)  
        try:
            product_result = shopify.sync_products(shop_domain, products_limit)
            sync_results["results"]["products"] = product_result
            if product_result.get('errors'):
                sync_results["warnings"].extend([f"Product: {err}" for err in product_result['errors']])
        except Exception as e:
            sync_results["errors"].append(f"Product sync failed: {str(e)}")
        
        # 3. Sync orders last (requires customers and products)
        try:
            order_result = shopify.sync_orders(shop_domain, orders_limit)
            sync_results["results"]["orders"] = order_result
            if order_result.get('errors'):
                sync_results["warnings"].extend([f"Order: {err}" for err in order_result['errors']])
        except Exception as e:
            sync_results["errors"].append(f"Order sync failed: {str(e)}")
        
        sync_results["sync_completed_at"] = datetime.now().isoformat()
        
        # Calculate summary stats
        total_synced = (
            sync_results["results"].get("customers", {}).get("customers_synced", 0) +
            sync_results["results"].get("orders", {}).get("orders_synced", 0) +
            sync_results["results"].get("products", {}).get("products_synced", 0)
        )
        
        return {
            "success": True,
            "message": f"Full sync completed for {shop_domain}",
            "data": sync_results,
            "summary": {
                "total_records_synced": total_synced,
                "has_errors": len(sync_results["errors"]) > 0,
                "has_warnings": len(sync_results["warnings"]) > 0
            },
            "next_steps": [
                "Check analytics/cross-platform-insights for unified reporting",
                "Run CLV analysis with analytics/clv/ml-predictions",
                "Use forecasting/revenue/forecast for predictions with real data"
            ]
        }
        
    except Exception as e:
        logger.error(f"Full sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Full sync failed: {str(e)}")

@router.get("/shopify/demo-setup")
def setup_shopify_demo(current_user: dict = Depends(get_current_user)):
    """
    Set up demo Shopify connection with simulated data for testing
    
    This creates a demo store connection and populates it with sample data
    for users who don't have access to a real Shopify store.
    """
    try:
        # Create demo shop connection
        demo_shop = "nexus-analytics-demo"
        
        # Simulate connecting to demo store
        from sqlalchemy import text
        from database import engine
        
        demo_connection = {
            'shop_domain': demo_shop,
            'access_token': 'demo_token_for_testing',  # Not a real token
            'status': 'demo'
        }
        
        query = """
        INSERT INTO shopify_connections (shop_domain, access_token, created_at, status)
        VALUES (:shop_domain, :access_token, NOW(), :status)
        ON CONFLICT (shop_domain) 
        DO UPDATE SET status = :status, updated_at = NOW()
        """
        
        with engine.connect() as conn:
            conn.execute(text(query), demo_connection)
            conn.commit()
        
        # Generate sample Shopify-style data
        demo_data = _generate_shopify_demo_data(demo_shop)
        
        return {
            "success": True,
            "message": "Demo Shopify store set up successfully",
            "data": {
                "demo_shop": demo_shop,
                "shop_url": f"https://{demo_shop}.myshopify.com",
                "demo_data_generated": demo_data,
                "status": "Ready for analytics testing"
            },
            "available_analytics": [
                "Cross-platform insights with demo Shopify data",
                "CLV predictions using Shopify customer patterns", 
                "Revenue forecasting with Shopify order data",
                "Customer segmentation across all platforms"
            ],
            "note": "This is a demo setup with simulated data for testing purposes"
        }
        
    except Exception as e:
        logger.error(f"Demo setup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo setup failed: {str(e)}")

def _generate_shopify_demo_data(shop_domain: str) -> Dict[str, int]:
    """Generate realistic demo data for Shopify store testing"""
    from sqlalchemy import text
    from database import engine
    import random
    from datetime import datetime, timedelta
    
    # Demo customers
    demo_customers = []
    for i in range(25):
        customer = {
            'external_id': f"shopify_demo_customer_{i}",
            'platform': 'shopify',
            'first_name': f"Demo{i}",
            'last_name': f"Customer{i}",
            'email': f"demo{i}@shopify-demo.com",
            'phone': f"+1555000{i:04d}",
            'created_at': (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
            'updated_at': datetime.now().isoformat(),
            'total_spent': random.uniform(100, 2000),
            'orders_count': random.randint(1, 10),
            'last_order_date': (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
        }
        demo_customers.append(customer)
    
    # Insert demo customers
    customer_query = """
    INSERT INTO universal_customers 
    (external_id, platform, first_name, last_name, email, phone, created_at, updated_at, total_spent, orders_count, last_order_date)
    VALUES (:external_id, :platform, :first_name, :last_name, :email, :phone, :created_at, :updated_at, :total_spent, :orders_count, :last_order_date)
    ON CONFLICT (external_id, platform) DO NOTHING
    """
    
    customers_added = 0
    with engine.connect() as conn:
        for customer in demo_customers:
            try:
                conn.execute(text(customer_query), customer)
                customers_added += 1
            except:
                pass
        conn.commit()
    
    return {
        "customers_added": customers_added,
        "shop_domain": shop_domain,
        "data_type": "demo"
    }