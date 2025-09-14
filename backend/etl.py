import pandas as pd
from sqlalchemy import create_engine

# Example ETL function
def run_etl(customers_csv, orders_csv, order_items_csv, db_url):
    # Load CSVs
    customers = pd.read_csv(customers_csv)
    orders = pd.read_csv(orders_csv)
    order_items = pd.read_csv(order_items_csv)


    # Calculate sales totals per customer
    sales_per_order = order_items.groupby('order_id')['price'].sum().reset_index()
    orders_with_total = pd.merge(orders, sales_per_order, on='order_id', how='left')
    orders_with_total.rename(columns={'price': 'order_total'}, inplace=True)

    sales_per_customer = orders_with_total.groupby('customer_id')['order_total'].sum().reset_index()
    sales_per_customer = pd.merge(customers, sales_per_customer, on='customer_id', how='left').fillna({'order_total': 0})

    # Create customer segments based on total sales
    def segment(sales):
        if sales >= 200:
            return 'VIP'
        elif sales >= 100:
            return 'Regular'
        else:
            return 'New'
    sales_per_customer['segment'] = sales_per_customer['order_total'].apply(segment)

    # Load to database
    engine = create_engine(db_url)
    customers.to_sql('customers', engine, if_exists='replace', index=False)
    orders_with_total.to_sql('orders', engine, if_exists='replace', index=False)
    order_items.to_sql('order_items', engine, if_exists='replace', index=False)
    sales_per_customer.to_sql('customer_segments', engine, if_exists='replace', index=False)

    print('ETL complete. Sales totals and customer segments calculated.')

run_etl('backend/customers.csv', 'backend/orders.csv', 'backend/order_items.csv', 'postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db')