from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from backend.auth import router as auth_router


app = FastAPI()
app.include_router(auth_router)

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