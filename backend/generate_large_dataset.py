"""
Large Dataset Generator for Customer Segmentation Testing

This script generates a comprehensive dataset with diverse customer scenarios
to showcase all segmentation features including:
- All 11 RFM segments (Champions, Loyal Customers, etc.)
- Various purchase patterns and customer lifecycles
- Multiple platforms and product categories
- Realistic time-based purchasing behavior
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from faker import Faker
import uuid

# Initialize Faker for realistic data
fake = Faker()
Faker.seed(42)  # For reproducible results
np.random.seed(42)
random.seed(42)

# Configuration
NUM_CUSTOMERS = 500
NUM_PRODUCTS = 100
NUM_ORDERS = 2000
PLATFORMS = ['shopify', 'woocommerce', 'magento', 'generic_csv', 'amazon']
CATEGORIES = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports', 'Beauty', 'Toys', 'Food']

# Date ranges
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=730)  # 2 years of data

def generate_customers(num_customers):
    """Generate diverse customer profiles"""
    customers = []
    
    # Define customer archetypes to ensure all segments are represented
    archetypes = [
        # Champions - High R, F, M
        {'weight': 0.08, 'recency_range': (1, 30), 'frequency_range': (8, 20), 'monetary_range': (1000, 5000)},
        
        # Loyal Customers - High F, M, varying R
        {'weight': 0.12, 'recency_range': (1, 60), 'frequency_range': (6, 15), 'monetary_range': (800, 3000)},
        
        # Potential Loyalists - High R, M, medium F
        {'weight': 0.10, 'recency_range': (1, 45), 'frequency_range': (3, 8), 'monetary_range': (500, 2000)},
        
        # New Customers - High R, low F, varying M
        {'weight': 0.15, 'recency_range': (1, 30), 'frequency_range': (1, 3), 'monetary_range': (50, 800)},
        
        # Promising - Medium R, low F, low M
        {'weight': 0.12, 'recency_range': (31, 90), 'frequency_range': (1, 3), 'monetary_range': (100, 500)},
        
        # Need Attention - Medium R, F, M
        {'weight': 0.10, 'recency_range': (61, 120), 'frequency_range': (3, 6), 'monetary_range': (300, 1000)},
        
        # About to Sleep - Low R, high F, M
        {'weight': 0.08, 'recency_range': (121, 200), 'frequency_range': (4, 10), 'monetary_range': (500, 2000)},
        
        # At Risk - Low R, high F, M
        {'weight': 0.07, 'recency_range': (201, 300), 'frequency_range': (5, 12), 'monetary_range': (800, 3000)},
        
        # Cannot Lose Them - Very low R, very high F, high M
        {'weight': 0.05, 'recency_range': (301, 400), 'frequency_range': (10, 25), 'monetary_range': (2000, 8000)},
        
        # Hibernating - Very low R, medium F, medium M
        {'weight': 0.08, 'recency_range': (400, 600), 'frequency_range': (2, 5), 'monetary_range': (200, 800)},
        
        # Lost - Very low R, low F, low M
        {'weight': 0.05, 'recency_range': (600, 730), 'frequency_range': (1, 2), 'monetary_range': (50, 300)},
    ]
    
    for i in range(num_customers):
        # Select archetype based on weights
        archetype = np.random.choice(archetypes, p=[a['weight'] for a in archetypes])
        
        customer = {
            'id': i + 1,  # Use integer ID
            'external_id': f"EXT_{i+1:04d}",
            'platform': random.choice(PLATFORMS),
            'email': fake.email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'full_name': None,  # Will be calculated
            'phone': fake.phone_number(),
            'created_at': fake.date_between(start_date=START_DATE, end_date=END_DATE - timedelta(days=30)),
            'updated_at': None,
            'platform_created_at': None,
            'address_line_1': fake.street_address(),
            'address_line_2': None,
            'city': fake.city(),
            'state': fake.state(),
            'country': fake.country(),
            'postal_code': fake.postcode(),
            'archetype': archetype,  # For reference during order generation
            'total_spent': 0,  # Will be calculated
            'orders_count': 0,  # Will be calculated
            'average_order_value': 0,  # Will be calculated
            'last_order_date': None,  # Will be set during order generation
            'is_active': True,
            'customer_lifetime_days': 0,  # Temporary field for calculation
        }
        
        customers.append(customer)
    
    return customers

def generate_products(num_products):
    """Generate product catalog"""
    products = []
    
    for i in range(num_products):
        category = random.choice(CATEGORIES)
        base_price = np.random.lognormal(mean=4, sigma=1)  # Log-normal distribution for realistic pricing
        
        product = {
            'id': i + 1,  # Use integer ID
            'external_id': f"EXT_PROD_{i+1:04d}",
            'platform': random.choice(PLATFORMS),
            'name': f"{fake.word().title()} {category} {fake.word().title()}",
            'description': fake.text(max_nb_chars=200),
            'sku': f"SKU-{category[:3].upper()}-{i+1:04d}",
            'barcode': None,
            'price': round(base_price, 2),
            'cost': round(base_price * 0.6, 2),  # 40% margin
            'compare_at_price': None,
            'category': category,
            'subcategory': None,
            'brand': fake.company(),
            'vendor': fake.company(),
            'product_type': category,
            'tags': f"{category}, {fake.word()}",
            'inventory_quantity': random.randint(0, 1000),
            'track_inventory': True,
            'is_active': random.choice([True, True, True, False]),  # 75% active
            'is_published': True,
            'created_at': fake.date_time_between(start_date=START_DATE, end_date=END_DATE),
            'updated_at': None,
            'platform_created_at': None,
            'total_sales': 0,  # Will be calculated
            'units_sold': 0,  # Will be calculated
        }
        
        products.append(product)
    
    return products

def generate_orders_and_items(customers, products, num_orders):
    """Generate orders and order items based on customer archetypes"""
    orders = []
    order_items = []
    order_id_counter = 1
    
    for customer in customers:
        archetype = customer['archetype']
        
        # Determine number of orders for this customer based on archetype
        min_freq, max_freq = archetype['frequency_range']
        num_customer_orders = random.randint(min_freq, max_freq)
        
        # Determine recency (days since last order)
        min_recency, max_recency = archetype['recency_range']
        days_since_last_order = random.randint(min_recency, max_recency)
        
        # Generate orders for this customer
        customer_orders = []
        total_spent = 0
        
        for order_num in range(num_customer_orders):
            # Calculate order date (spread orders over time, with most recent based on recency)
            if order_num == 0:  # Most recent order
                order_date = END_DATE - timedelta(days=days_since_last_order)
            else:
                # Previous orders spread over the customer's lifetime
                days_back = days_since_last_order + random.randint(30, 365)
                order_date = END_DATE - timedelta(days=days_back)
            
            # Ensure order date is not before customer joined
            customer_joined = customer['created_at']
            if isinstance(customer_joined, datetime):
                customer_joined_dt = customer_joined
            else:
                customer_joined_dt = datetime.combine(customer_joined, datetime.min.time())
            
            if order_date < customer_joined_dt:
                order_date = customer_joined_dt + timedelta(days=random.randint(1, 30))
            
            # Generate order value based on archetype monetary range
            min_monetary, max_monetary = archetype['monetary_range']
            if num_customer_orders > 1:
                target_total = random.uniform(min_monetary, max_monetary)
                order_value = target_total / num_customer_orders * random.uniform(0.5, 2.0)  # Add some variation
            else:
                order_value = random.uniform(min_monetary, max_monetary)
            
            order = {
                'id': order_id_counter,  # Use integer ID
                'external_id': f"EXT_ORD_{order_id_counter:06d}",
                'platform': customer['platform'],
                'customer_id': customer['id'],
                'customer_external_id': customer['external_id'],
                'order_number': f"ORD-{order_id_counter:06d}",
                'order_date': order_date,
                'subtotal': 0,  # Will be calculated
                'tax_amount': 0,  # Will be calculated
                'shipping_amount': round(random.uniform(0, 25), 2),
                'discount_amount': round(random.uniform(0, order_value * 0.2), 2),  # Up to 20% discount
                'total_amount': 0,  # Will be calculated from items
                'currency': 'USD',
                'status': random.choice(['completed', 'completed', 'completed', 'pending', 'cancelled']),  # 60% completed
                'fulfillment_status': random.choice(['fulfilled', 'partial', 'unfulfilled']),
                'payment_status': random.choice(['paid', 'pending', 'refunded']),
                'shipping_method': random.choice(['standard', 'express', 'overnight']),
                'tracking_number': None,
                'email': customer['email'],
                'phone': customer['phone'],
                'created_at': order_date,
                'updated_at': None,
                'shipped_at': None,
                'delivered_at': None,
            }
            
            orders.append(order)
            customer_orders.append(order)
            
            # Generate order items
            num_items = random.randint(1, 5)  # 1-5 items per order
            order_total = 0
            
            for item_num in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 3)
                unit_price = product['price'] * random.uniform(0.8, 1.2)  # Price variation
                
                order_item = {
                    'id': int(f"{order_id_counter}{item_num+1:02d}"),  # Use integer ID
                    'external_id': f"ITEM_{order_id_counter}_{item_num+1:02d}",
                    'platform': customer['platform'],
                    'order_id': order['id'],
                    'product_id': product['id'],
                    'order_external_id': order['external_id'],
                    'product_external_id': product['external_id'],
                    'product_name': product['name'],
                    'product_sku': product['sku'],
                    'variant_title': None,
                    'quantity': quantity,
                    'unit_price': round(unit_price, 2),
                    'total_price': round(unit_price * quantity, 2),
                    'discount_amount': round(unit_price * quantity * 0.1 * random.random(), 2),
                    'tax_amount': round(unit_price * quantity * 0.08, 2),  # 8% tax
                    'fulfillment_status': 'fulfilled' if order['status'] == 'completed' else 'unfulfilled',
                    'quantity_fulfilled': quantity if order['status'] == 'completed' else 0,
                    'created_at': order_date,
                    'updated_at': None,
                }
                
                order_items.append(order_item)
                order_total += order_item['total_price']
            
            # Update order totals
            order['subtotal'] = round(order_total, 2)
            order['tax_amount'] = round(order_total * 0.08, 2)  # 8% tax
            order['total_amount'] = round(order_total + order['tax_amount'] + order['shipping_amount'] - order['discount_amount'], 2)
            
            if order['status'] == 'completed':
                total_spent += order['total_amount']
            
            order_id_counter += 1
        
        # Update customer aggregates
        customer['total_spent'] = round(total_spent, 2)
        customer['orders_count'] = len([o for o in customer_orders if o['status'] == 'completed'])
        customer['last_order_date'] = max([o['order_date'] for o in customer_orders]) if customer_orders else customer['created_at']
        customer['average_order_value'] = round(total_spent / max(customer['orders_count'], 1), 2)
        customer['full_name'] = f"{customer['first_name']} {customer['last_name']}".strip()
        customer['updated_at'] = datetime.now()
        customer['platform_created_at'] = customer['created_at']
        
        # Remove archetype and temporary fields
        del customer['archetype']
        if 'customer_lifetime_days' in customer:
            del customer['customer_lifetime_days']
    
    return orders, order_items

def save_to_database():
    """Save generated data to the PostgreSQL database"""
    from sqlalchemy import create_engine, text
    
    # Database connection
    DB_URL = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"
    engine = create_engine(DB_URL)
    
    print("🎯 Generating large dataset...")
    
    # Generate data
    print("   📊 Generating customers...")
    customers = generate_customers(NUM_CUSTOMERS)
    
    print("   🛍️  Generating products...")
    products = generate_products(NUM_PRODUCTS)
    
    print("   📦 Generating orders and items...")
    orders, order_items = generate_orders_and_items(customers, products, NUM_ORDERS)
    
    print(f"   ✅ Generated: {len(customers)} customers, {len(products)} products, {len(orders)} orders, {len(order_items)} items")
    
    # Convert to DataFrames
    customers_df = pd.DataFrame(customers)
    products_df = pd.DataFrame(products)
    orders_df = pd.DataFrame(orders)
    order_items_df = pd.DataFrame(order_items)
    
    # Save to database
    with engine.connect() as conn:
        print("   🗄️  Clearing existing data...")
        # Delete in proper order to avoid foreign key constraints
        conn.execute(text("DELETE FROM universal_customer_segments"))
        conn.execute(text("DELETE FROM universal_order_items"))
        conn.execute(text("DELETE FROM universal_orders"))
        conn.execute(text("DELETE FROM universal_products"))
        conn.execute(text("DELETE FROM universal_customers"))
        conn.commit()
        
        print("   💾 Inserting new data...")
        customers_df.to_sql('universal_customers', conn, if_exists='append', index=False)
        products_df.to_sql('universal_products', conn, if_exists='append', index=False)
        orders_df.to_sql('universal_orders', conn, if_exists='append', index=False)
        order_items_df.to_sql('universal_order_items', conn, if_exists='append', index=False)
        conn.commit()
    
    print("   🎉 Database updated successfully!")
    
    # Print summary statistics
    print("\n📈 Dataset Summary:")
    print(f"   • Customers: {len(customers)} across {len(set(c['platform'] for c in customers))} platforms")
    print(f"   • Products: {len(products)} across {len(set(p['category'] for p in products))} categories")
    print(f"   • Orders: {len(orders)} ({len([o for o in orders if o['status'] == 'completed'])} completed)")
    print(f"   • Order Items: {len(order_items)}")
    
    # Customer statistics
    total_revenue = sum(c['total_spent'] for c in customers)
    avg_customer_value = total_revenue / len(customers)
    customers_by_orders = {}
    for c in customers:
        orders_count = c['orders_count']
        if orders_count not in customers_by_orders:
            customers_by_orders[orders_count] = 0
        customers_by_orders[orders_count] += 1
    
    print(f"   • Total Revenue: ${total_revenue:,.2f}")
    print(f"   • Average Customer Value: ${avg_customer_value:.2f}")
    print(f"   • Customer Distribution by Order Count: {dict(sorted(customers_by_orders.items()))}")
    
    return customers_df, products_df, orders_df, order_items_df

def preview_segmentation_results():
    """Preview what the segmentation analysis will show"""
    print("\n🔍 Previewing Expected Segmentation Results...")
    
    # This will be populated after running the segmentation
    print("   📊 Expected segments to be represented:")
    segments = [
        "Champions (High R,F,M)", "Loyal Customers (High F,M)", 
        "Potential Loyalists (High R,M)", "New Customers (High R, Low F)",
        "Promising (Medium R, Low F,M)", "Need Attention (Medium R,F,M)",
        "About to Sleep (Low R, High F,M)", "At Risk (Low R, High F,M)",
        "Cannot Lose Them (Very Low R, Very High F,M)", "Hibernating (Very Low R, Medium F,M)",
        "Lost (Very Low R, Low F,M)"
    ]
    
    for i, segment in enumerate(segments, 1):
        print(f"      {i:2d}. {segment}")
    
    print(f"\n   🎯 With {NUM_CUSTOMERS} customers, we should see:")
    print(f"      • Rich clustering patterns in ML analysis")
    print(f"      • All RFM segments populated")
    print(f"      • Diverse churn risk distribution")
    print(f"      • Meaningful business insights")

if __name__ == "__main__":
    try:
        # Generate and save data
        customers_df, products_df, orders_df, order_items_df = save_to_database()
        
        # Preview expected results
        preview_segmentation_results()
        
        print(f"\n🚀 Ready to test! Start your servers and visit:")
        print(f"   🔗 Analytics Dashboard: http://localhost:3000/analytics")
        print(f"   🔗 Segmentation Page: http://localhost:3000/segmentation") 
        print(f"   🔗 API Documentation: http://localhost:8001/docs")
        
    except Exception as e:
        print(f"❌ Error generating dataset: {e}")
        import traceback
        traceback.print_exc()