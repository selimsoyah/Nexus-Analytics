from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from auth import router as auth_router
from api_enhanced import router as enhanced_router


app = FastAPI(
    title="Nexus Analytics API",
    description="Modular E-commerce Analytics Platform",
    version="2.0.0"
)

# Include routers
app.include_router(auth_router)
app.include_router(enhanced_router, prefix="/v2", tags=["Enhanced Analytics"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# Database connection string
DB_URL = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"
engine = create_engine(DB_URL)

# Endpoint to fetch all customers
@app.get("/customers")
def get_customers():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM customers"))
        customers = [dict(row) for row in result.mappings()]
    return {"customers": customers}

# Endpoint to fetch all orders
@app.get("/orders")
def get_orders():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM orders"))
        orders = [dict(row) for row in result.mappings()]
    return {"orders": orders}

# Endpoint to fetch all order items
@app.get("/order_items")
def get_order_items():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM order_items"))
        order_items = [dict(row) for row in result.mappings()]
    return {"order_items": order_items}
# Endpoint to fetch customer segments
@app.get("/customer_segments")
def get_customer_segments():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM customer_segments"))
        segments = [dict(row) for row in result.mappings()]
    return {"customer_segments": segments}

# === UNIVERSAL ENDPOINTS (Cross-Platform) ===

@app.get("/universal/customers")
def get_universal_customers(platform: str = None):
    """Get customers from universal schema - works across all platforms"""
    query = "SELECT * FROM universal_customers"
    params = {}
    
    if platform:
        query += " WHERE platform = :platform"
        params["platform"] = platform
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        customers = [dict(row) for row in result.mappings()]
    
    return {
        "customers": customers,
        "platform_filter": platform,
        "total_count": len(customers)
    }

@app.get("/universal/products")
def get_universal_products(platform: str = None, category: str = None):
    """Get products from universal schema - works across all platforms"""
    query = "SELECT * FROM universal_products WHERE 1=1"
    params = {}
    
    if platform:
        query += " AND platform = :platform"
        params["platform"] = platform
        
    if category:
        query += " AND category ILIKE :category"
        params["category"] = f"%{category}%"
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        products = [dict(row) for row in result.mappings()]
    
    return {
        "products": products,
        "filters": {"platform": platform, "category": category},
        "total_count": len(products)
    }

@app.get("/universal/orders")
def get_universal_orders(platform: str = None):
    """Get orders from universal schema - works across all platforms"""
    query = """
    SELECT 
        o.*,
        c.first_name || ' ' || c.last_name as customer_name,
        c.email as customer_email
    FROM universal_orders o
    LEFT JOIN universal_customers c ON o.customer_id = c.id
    WHERE 1=1
    """
    params = {}
    
    if platform:
        query += " AND o.platform = :platform"
        params["platform"] = platform
    
    query += " ORDER BY o.order_date DESC"
    
    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        orders = [dict(row) for row in result.mappings()]
    
    return {
        "orders": orders,
        "platform_filter": platform,
        "total_count": len(orders)
    }

@app.get("/universal/analytics/overview")
def get_cross_platform_overview():
    """Get comprehensive analytics across all platforms"""
    with engine.connect() as conn:
        # Platform summary
        platform_stats = conn.execute(text("""
            SELECT 
                platform,
                COUNT(DISTINCT id) as total_customers,
                AVG(total_spent::numeric) as avg_customer_value
            FROM universal_customers 
            GROUP BY platform
        """))
        
        # Product performance across platforms
        product_stats = conn.execute(text("""
            SELECT 
                p.platform,
                COUNT(DISTINCT p.id) as total_products,
                AVG(p.price::numeric) as avg_product_price,
                COUNT(DISTINCT oi.id) as total_sales
            FROM universal_products p
            LEFT JOIN universal_order_items oi ON p.id = oi.product_id
            GROUP BY p.platform
        """))
        
        # Order trends
        order_stats = conn.execute(text("""
            SELECT 
                platform,
                COUNT(*) as total_orders,
                SUM(total_amount::numeric) as total_revenue,
                AVG(total_amount::numeric) as avg_order_value
            FROM universal_orders
            GROUP BY platform
        """))
        
        # Recent activity
        recent_orders = conn.execute(text("""
            SELECT 
                o.platform,
                o.order_date,
                o.total_amount,
                c.first_name || ' ' || c.last_name as customer_name
            FROM universal_orders o
            LEFT JOIN universal_customers c ON o.customer_id = c.id
            ORDER BY o.order_date DESC
            LIMIT 10
        """))
        
        return {
            "platform_summary": [dict(row) for row in platform_stats.mappings()],
            "product_performance": [dict(row) for row in product_stats.mappings()],
            "order_analytics": [dict(row) for row in order_stats.mappings()],
            "recent_activity": [dict(row) for row in recent_orders.mappings()],
            "timestamp": "2024-01-01T00:00:00"
        }