"""
Schema Inspector - Check database schema to match data generation
"""

from sqlalchemy import create_engine, inspect

# Database connection
DB_URL = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"
engine = create_engine(DB_URL)

def inspect_schema():
    inspector = inspect(engine)
    
    tables = ['universal_customers', 'universal_products', 'universal_orders', 'universal_order_items']
    
    for table_name in tables:
        if inspector.has_table(table_name):
            print(f"\n📋 Table: {table_name}")
            columns = inspector.get_columns(table_name)
            for col in columns:
                print(f"   • {col['name']}: {col['type']} {'(nullable)' if col['nullable'] else '(NOT NULL)'}")
        else:
            print(f"\n❌ Table {table_name} does not exist")

if __name__ == "__main__":
    inspect_schema()