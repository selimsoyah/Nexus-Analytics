"""
Enhanced Universal Analytics API

This module provides rich analytics endpoints that work across all platforms
using our modular universal schema.
"""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import create_engine, text
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta

router = APIRouter()

# Database connection
DB_URL = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"
engine = create_engine(DB_URL)

@router.get("/analytics/customer-insights/{customer_external_id}")
def get_customer_detailed_insights(
    customer_external_id: str,
    platform: Optional[str] = None
):
    """
    Get comprehensive customer insights including:
    - Basic info (name, email, total spent)
    - Purchase history with products and prices
    - Buying patterns and preferences
    """
    
    query = """
    SELECT 
        c.first_name,
        c.last_name,
        c.email,
        c.platform,
        c.total_spent,
        c.orders_count,
        c.average_order_value,
        c.last_order_date,
        
        -- Order details
        o.external_id as order_id,
        o.order_date,
        o.total_amount as order_total,
        o.status as order_status,
        
        -- Product details
        p.name as product_name,
        p.category as product_category,
        p.price as product_list_price,
        p.sku as product_sku,
        
        -- Purchase details
        oi.quantity,
        oi.unit_price,
        oi.total_price as line_total
        
    FROM universal_customers c
    LEFT JOIN universal_orders o ON c.id = o.customer_id
    LEFT JOIN universal_order_items oi ON o.id = oi.order_id
    LEFT JOIN universal_products p ON oi.product_id = p.id
    WHERE c.external_id = :customer_id
    """
    
    params = {"customer_id": customer_external_id}
    
    if platform:
        query += " AND c.platform = :platform"
        params["platform"] = platform
    
    query += " ORDER BY o.order_date DESC, p.name"
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            # Structure the response
            customer_info = {
                "customer_id": customer_external_id,
                "name": f"{rows[0][0]} {rows[0][1]}" if rows[0][0] else "Unknown",
                "email": rows[0][2],
                "platform": rows[0][3],
                "total_spent": float(rows[0][4] or 0),
                "orders_count": rows[0][5] or 0,
                "average_order_value": float(rows[0][6] or 0),
                "last_order_date": rows[0][7].isoformat() if rows[0][7] else None,
                "orders": []
            }
            
            # Group by orders
            orders_dict = {}
            for row in rows:
                if row[8]:  # order_id exists
                    order_id = row[8]
                    if order_id not in orders_dict:
                        orders_dict[order_id] = {
                            "order_id": order_id,
                            "order_date": row[9].isoformat() if row[9] else None,
                            "total_amount": float(row[10] or 0),
                            "status": row[11],
                            "products": []
                        }
                    
                    if row[12]:  # product exists
                        orders_dict[order_id]["products"].append({
                            "name": row[12],
                            "category": row[13],
                            "list_price": float(row[14] or 0),
                            "sku": row[15],
                            "quantity": row[16] or 0,
                            "unit_price": float(row[17] or 0),
                            "line_total": float(row[18] or 0)
                        })
            
            customer_info["orders"] = list(orders_dict.values())
            
            return customer_info
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/analytics/product-performance")
def get_product_performance_analytics(
    platform: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(default=20, le=100)
):
    """
    Get product performance analytics across platforms:
    - Sales volume and revenue
    - Customer reach and repeat purchases
    - Price performance vs list price
    """
    
    query = """
    SELECT 
        p.name,
        p.category,
        p.price as list_price,
        p.sku,
        p.platform,
        
        -- Sales metrics
        COUNT(oi.id) as times_purchased,
        SUM(oi.quantity) as total_units_sold,
        SUM(oi.total_price) as total_revenue,
        AVG(oi.unit_price) as avg_selling_price,
        MIN(oi.unit_price) as lowest_selling_price,
        MAX(oi.unit_price) as highest_selling_price,
        
        -- Customer metrics
        COUNT(DISTINCT o.customer_id) as unique_customers,
        COUNT(DISTINCT o.id) as unique_orders,
        
        -- Time metrics
        MIN(o.order_date) as first_sale_date,
        MAX(o.order_date) as last_sale_date
        
    FROM universal_products p
    JOIN universal_order_items oi ON p.id = oi.product_id
    JOIN universal_orders o ON oi.order_id = o.id
    WHERE 1=1
    """
    
    params = {}
    
    if platform:
        query += " AND p.platform = :platform"
        params["platform"] = platform
        
    if category:
        query += " AND p.category ILIKE :category"
        params["category"] = f"%{category}%"
    
    query += """
    GROUP BY p.id, p.name, p.category, p.price, p.sku, p.platform
    ORDER BY total_revenue DESC
    LIMIT :limit
    """
    params["limit"] = limit
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            columns = result.keys()
            rows = result.fetchall()
            
            products = []
            for row in rows:
                product_data = dict(zip(columns, row))
                
                # Convert decimals to floats for JSON serialization
                for key, value in product_data.items():
                    if hasattr(value, 'quantize'):  # Decimal type
                        product_data[key] = float(value)
                    elif isinstance(value, datetime):
                        product_data[key] = value.isoformat()
                
                # Calculate additional metrics
                if product_data['list_price'] and product_data['avg_selling_price']:
                    product_data['discount_rate'] = (
                        (product_data['list_price'] - product_data['avg_selling_price']) / 
                        product_data['list_price'] * 100
                    )
                
                if product_data['unique_customers'] and product_data['times_purchased']:
                    product_data['repeat_purchase_rate'] = (
                        (product_data['times_purchased'] - product_data['unique_customers']) /
                        product_data['times_purchased'] * 100
                    )
                
                products.append(product_data)
            
            return {
                "products": products,
                "total_products": len(products),
                "filters_applied": {
                    "platform": platform,
                    "category": category,
                    "limit": limit
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/analytics/cross-platform-insights")
def get_cross_platform_insights():
    """
    Get insights that span across multiple platforms:
    - Platform comparison metrics
    - Cross-platform customer behavior
    - Product performance across platforms
    """
    
    try:
        with engine.connect() as conn:
            # Platform overview
            platform_overview = conn.execute(text("""
                SELECT 
                    c.platform,
                    COUNT(DISTINCT c.id) as total_customers,
                    COUNT(DISTINCT o.id) as total_orders,
                    COUNT(DISTINCT p.id) as total_products,
                    SUM(o.total_amount) as total_revenue,
                    AVG(o.total_amount) as avg_order_value
                FROM universal_customers c
                LEFT JOIN universal_orders o ON c.id = o.customer_id
                LEFT JOIN universal_products p ON p.platform = c.platform
                GROUP BY c.platform
                ORDER BY total_revenue DESC
            """)).fetchall()
            
            # Top products across all platforms
            top_products = conn.execute(text("""
                SELECT 
                    p.name,
                    p.platform,
                    p.category,
                    SUM(oi.quantity) as total_units_sold,
                    SUM(oi.total_price) as total_revenue,
                    COUNT(DISTINCT o.customer_id) as unique_customers
                FROM universal_products p
                JOIN universal_order_items oi ON p.id = oi.product_id
                JOIN universal_orders o ON oi.order_id = o.id
                GROUP BY p.name, p.platform, p.category
                ORDER BY total_revenue DESC
                LIMIT 10
            """)).fetchall()
            
            # Category performance across platforms
            category_performance = conn.execute(text("""
                SELECT 
                    p.category,
                    p.platform,
                    COUNT(DISTINCT p.id) as product_count,
                    SUM(oi.quantity) as units_sold,
                    SUM(oi.total_price) as revenue
                FROM universal_products p
                JOIN universal_order_items oi ON p.id = oi.product_id
                WHERE p.category IS NOT NULL
                GROUP BY p.category, p.platform
                ORDER BY revenue DESC
            """)).fetchall()
            
            # Format response
            return {
                "platform_overview": [
                    {
                        "platform": row[0],
                        "customers": row[1],
                        "orders": row[2], 
                        "products": row[3],
                        "revenue": float(row[4] or 0),
                        "avg_order_value": float(row[5] or 0)
                    }
                    for row in platform_overview
                ],
                "top_products_cross_platform": [
                    {
                        "name": row[0],
                        "platform": row[1], 
                        "category": row[2],
                        "units_sold": row[3],
                        "revenue": float(row[4]),
                        "unique_customers": row[5]
                    }
                    for row in top_products
                ],
                "category_performance": [
                    {
                        "category": row[0],
                        "platform": row[1],
                        "product_count": row[2],
                        "units_sold": row[3],
                        "revenue": float(row[4])
                    }
                    for row in category_performance
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/analytics/customer-segments-detailed")
def get_detailed_customer_segments(platform: Optional[str] = None):
    """
    Get detailed customer segmentation with purchase behavior insights
    """
    
    query = """
    SELECT 
        cs.segment,
        COUNT(DISTINCT c.id) as customer_count,
        AVG(c.total_spent) as avg_total_spent,
        AVG(c.orders_count) as avg_order_count,
        AVG(c.average_order_value) as avg_order_value,
        
        -- Top products for each segment
        (
            SELECT STRING_AGG(DISTINCT p.name, ', ')
            FROM universal_orders o2
            JOIN universal_order_items oi2 ON o2.id = oi2.order_id
            JOIN universal_products p ON oi2.product_id = p.id
            WHERE o2.customer_id = c.id
            GROUP BY o2.customer_id
            ORDER BY SUM(oi2.total_price) DESC
            LIMIT 1
        ) as top_products,
        
        c.platform
        
    FROM universal_customer_segments cs
    JOIN universal_customers c ON cs.customer_id = c.id
    WHERE 1=1
    """
    
    params = {}
    if platform:
        query += " AND c.platform = :platform"
        params["platform"] = platform
    
    query += """
    GROUP BY cs.segment, c.platform
    ORDER BY avg_total_spent DESC
    """
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            return {
                "segments": [
                    {
                        "segment": row[0],
                        "customer_count": row[1],
                        "avg_total_spent": float(row[2] or 0),
                        "avg_order_count": float(row[3] or 0),
                        "avg_order_value": float(row[4] or 0),
                        "top_products": row[5],
                        "platform": row[6]
                    }
                    for row in rows
                ]
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")