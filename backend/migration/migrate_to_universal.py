"""
Data Migration Script: Legacy to Universal Schema

This script migrates existing data from the current format to the new universal schema,
while maintaining backward compatibility with existing APIs.
"""

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from decimal import Decimal
import logging

# Import universal schemas
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.universal import (
    Base, UniversalCustomer, UniversalProduct, UniversalOrder, 
    UniversalOrderItem, UniversalCustomerSegment
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataMigrator:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def create_universal_tables(self):
        """Create universal tables alongside existing ones"""
        logger.info("Creating universal database tables...")
        Base.metadata.create_all(self.engine)
        logger.info("Universal tables created successfully!")
        
    def migrate_customers(self, platform_name: str = "generic_csv"):
        """Migrate customers from legacy format to universal format"""
        logger.info("Migrating customers to universal format...")
        
        session = self.Session()
        try:
            # Load existing customers data
            customers_df = pd.read_sql("SELECT * FROM customers", self.engine)
            
            for _, row in customers_df.iterrows():
                # Check if customer already exists
                existing = session.query(UniversalCustomer).filter_by(
                    external_id=str(row['customer_id']), 
                    platform=platform_name
                ).first()
                
                if existing:
                    continue  # Skip if already migrated
                
                # Parse customer name if it's a full name
                full_name = row['customer_name']
                name_parts = full_name.split(' ', 1) if full_name else ['', '']
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                # Create universal customer
                universal_customer = UniversalCustomer(
                    external_id=str(row['customer_id']),
                    platform=platform_name,
                    email=row['email'],
                    first_name=first_name,
                    last_name=last_name,
                    full_name=full_name,
                    platform_created_at=datetime.utcnow() - timedelta(days=30)  # Estimate
                )
                
                session.add(universal_customer)
            
            session.commit()
            logger.info(f"Successfully migrated {len(customers_df)} customers")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error migrating customers: {e}")
            raise
        finally:
            session.close()
    
    def migrate_products(self, platform_name: str = "generic_csv"):
        """Extract and migrate products from order_items"""
        logger.info("Migrating products to universal format...")
        
        session = self.Session()
        try:
            # Extract unique products from order_items
            products_df = pd.read_sql("""
                SELECT DISTINCT product as name, 
                       product as external_id,
                       AVG(price) as avg_price
                FROM order_items 
                GROUP BY product
            """, self.engine)
            
            for _, row in products_df.iterrows():
                # Check if product already exists
                existing = session.query(UniversalProduct).filter_by(
                    external_id=row['external_id'],
                    platform=platform_name
                ).first()
                
                if existing:
                    continue
                
                # Create universal product
                universal_product = UniversalProduct(
                    external_id=row['external_id'],
                    platform=platform_name,
                    name=row['name'],
                    sku=row['external_id'],  # Use product name as SKU for now
                    price=Decimal(str(row['avg_price'])),
                    category="General",  # Default category
                    platform_created_at=datetime.utcnow() - timedelta(days=60)
                )
                
                session.add(universal_product)
            
            session.commit()
            logger.info(f"Successfully migrated {len(products_df)} products")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error migrating products: {e}")
            raise
        finally:
            session.close()
    
    def migrate_orders(self, platform_name: str = "generic_csv"):
        """Migrate orders from legacy format to universal format"""
        logger.info("Migrating orders to universal format...")
        
        session = self.Session()
        try:
            # Load existing orders data with customer info
            orders_df = pd.read_sql("""
                SELECT o.*, c.email 
                FROM orders o 
                LEFT JOIN customers c ON o.customer_id = c.customer_id
            """, self.engine)
            
            for _, row in orders_df.iterrows():
                # Check if order already exists
                existing = session.query(UniversalOrder).filter_by(
                    external_id=str(row['order_id']),
                    platform=platform_name
                ).first()
                
                if existing:
                    continue
                
                # Get corresponding universal customer
                universal_customer = session.query(UniversalCustomer).filter_by(
                    external_id=str(row['customer_id']),
                    platform=platform_name
                ).first()
                
                # Parse order date
                order_date = pd.to_datetime(row['order_date'])
                
                # Create universal order
                universal_order = UniversalOrder(
                    external_id=str(row['order_id']),
                    platform=platform_name,
                    customer_id=universal_customer.id if universal_customer else None,
                    customer_external_id=str(row['customer_id']),
                    order_number=f"ORD-{row['order_id']}",
                    order_date=order_date,
                    subtotal=Decimal(str(row['total'])),
                    total_amount=Decimal(str(row['total'])),
                    status="completed",  # Assume completed for historical data
                    fulfillment_status="fulfilled",
                    payment_status="paid",
                    email=row.get('email'),
                    currency="USD"
                )
                
                session.add(universal_order)
            
            session.commit()
            logger.info(f"Successfully migrated {len(orders_df)} orders")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error migrating orders: {e}")
            raise
        finally:
            session.close()
    
    def migrate_order_items(self, platform_name: str = "generic_csv"):
        """Migrate order items from legacy format to universal format"""
        logger.info("Migrating order items to universal format...")
        
        session = self.Session()
        try:
            # Load existing order items
            order_items_df = pd.read_sql("SELECT * FROM order_items", self.engine)
            
            for _, row in order_items_df.iterrows():
                # Check if order item already exists
                existing = session.query(UniversalOrderItem).filter_by(
                    external_id=str(row['order_item_id']),
                    platform=platform_name
                ).first()
                
                if existing:
                    continue
                
                # Get corresponding universal order and product
                universal_order = session.query(UniversalOrder).filter_by(
                    external_id=str(row['order_id']),
                    platform=platform_name
                ).first()
                
                universal_product = session.query(UniversalProduct).filter_by(
                    external_id=row['product'],
                    platform=platform_name
                ).first()
                
                # Calculate total price
                unit_price = Decimal(str(row['price']))
                quantity = int(row['quantity'])
                total_price = unit_price * quantity
                
                # Create universal order item
                universal_order_item = UniversalOrderItem(
                    external_id=str(row['order_item_id']),
                    platform=platform_name,
                    order_id=universal_order.id if universal_order else None,
                    product_id=universal_product.id if universal_product else None,
                    order_external_id=str(row['order_id']),
                    product_external_id=row['product'],
                    product_name=row['product'],
                    product_sku=row['product'],
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                    fulfillment_status="fulfilled"
                )
                
                session.add(universal_order_item)
            
            session.commit()
            logger.info(f"Successfully migrated {len(order_items_df)} order items")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error migrating order items: {e}")
            raise
        finally:
            session.close()
    
    def calculate_customer_metrics(self):
        """Calculate customer metrics for universal customers"""
        logger.info("Calculating customer metrics...")
        
        session = self.Session()
        try:
            # Get all universal customers
            customers = session.query(UniversalCustomer).all()
            
            for customer in customers:
                # Calculate metrics from orders
                orders = session.query(UniversalOrder).filter_by(customer_id=customer.id).all()
                
                if orders:
                    customer.orders_count = len(orders)
                    customer.total_spent = sum(order.total_amount for order in orders)
                    customer.average_order_value = customer.total_spent / customer.orders_count
                    customer.last_order_date = max(order.order_date for order in orders)
                else:
                    customer.orders_count = 0
                    customer.total_spent = Decimal('0')
                    customer.average_order_value = Decimal('0')
                    
            session.commit()
            logger.info(f"Updated metrics for {len(customers)} customers")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error calculating customer metrics: {e}")
            raise
        finally:
            session.close()
    
    def migrate_customer_segments(self, platform_name: str = "generic_csv"):
        """Migrate customer segments to universal format"""
        logger.info("Migrating customer segments...")
        
        session = self.Session()
        try:
            # Load existing customer segments
            segments_df = pd.read_sql("SELECT * FROM customer_segments", self.engine)
            
            for _, row in segments_df.iterrows():
                # Get corresponding universal customer
                universal_customer = session.query(UniversalCustomer).filter_by(
                    external_id=str(row['customer_id']),
                    platform=platform_name
                ).first()
                
                if not universal_customer:
                    continue
                
                # Check if segment already exists
                existing = session.query(UniversalCustomerSegment).filter_by(
                    customer_id=universal_customer.id
                ).first()
                
                if existing:
                    continue
                
                # Map segment score
                segment_scores = {'VIP': 5.0, 'Regular': 3.0, 'New': 1.0}
                segment_score = segment_scores.get(row['segment'], 2.0)
                
                # Create universal customer segment
                universal_segment = UniversalCustomerSegment(
                    customer_id=universal_customer.id,
                    segment=row['segment'],
                    segment_score=Decimal(str(segment_score)),
                    total_orders=universal_customer.orders_count,
                    total_spent=universal_customer.total_spent,
                    average_order_value=universal_customer.average_order_value,
                    days_since_last_order=0,  # Calculate based on last_order_date if needed
                    lifetime_value_score=segment_score
                )
                
                session.add(universal_segment)
            
            session.commit()
            logger.info(f"Successfully migrated {len(segments_df)} customer segments")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error migrating customer segments: {e}")
            raise
        finally:
            session.close()
    
    def verify_migration(self):
        """Verify that migration was successful"""
        logger.info("Verifying migration...")
        
        # Count records in each universal table
        with self.engine.connect() as conn:
            customers_count = conn.execute(text("SELECT COUNT(*) FROM universal_customers")).scalar()
            products_count = conn.execute(text("SELECT COUNT(*) FROM universal_products")).scalar()
            orders_count = conn.execute(text("SELECT COUNT(*) FROM universal_orders")).scalar()
            order_items_count = conn.execute(text("SELECT COUNT(*) FROM universal_order_items")).scalar()
            segments_count = conn.execute(text("SELECT COUNT(*) FROM universal_customer_segments")).scalar()
            
            logger.info(f"Migration Summary:")
            logger.info(f"  Universal Customers: {customers_count}")
            logger.info(f"  Universal Products: {products_count}")
            logger.info(f"  Universal Orders: {orders_count}")
            logger.info(f"  Universal Order Items: {order_items_count}")
            logger.info(f"  Universal Customer Segments: {segments_count}")
    
    def run_full_migration(self, platform_name: str = "generic_csv"):
        """Run the complete migration process"""
        logger.info("Starting full migration to universal schema...")
        
        try:
            # Create tables
            self.create_universal_tables()
            
            # Migrate data in order (respecting foreign key dependencies)
            self.migrate_customers(platform_name)
            self.migrate_products(platform_name)
            self.migrate_orders(platform_name)
            self.migrate_order_items(platform_name)
            
            # Calculate metrics
            self.calculate_customer_metrics()
            
            # Migrate segments
            self.migrate_customer_segments(platform_name)
            
            # Verify migration
            self.verify_migration()
            
            logger.info("✅ Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise


if __name__ == "__main__":
    # Database connection string
    DB_URL = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"
    
    # Initialize migrator
    migrator = DataMigrator(DB_URL)
    
    # Run migration
    migrator.run_full_migration(platform_name="generic_csv")