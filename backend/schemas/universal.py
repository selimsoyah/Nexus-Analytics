"""
Universal Database Schemas for Multi-Platform E-commerce Analytics

This module defines platform-agnostic data models that can accommodate
data from any e-commerce platform (Shopify, WooCommerce, Magento, etc.)
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class UniversalCustomer(Base):
    """
    Universal customer model that accommodates data from any e-commerce platform
    """
    __tablename__ = "universal_customers"
    
    # Internal ID (auto-increment)
    id = Column(Integer, primary_key=True)
    
    # Platform-specific information
    external_id = Column(String, nullable=False)  # Original platform customer ID
    platform = Column(String, nullable=False)    # 'shopify', 'woocommerce', 'generic_csv', etc.
    
    # Universal customer fields
    email = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    full_name = Column(String)  # Some platforms provide full name instead of split
    phone = Column(String)
    
    # Address information (common across platforms)
    address_line_1 = Column(String)
    address_line_2 = Column(String)
    city = Column(String)
    state = Column(String)
    country = Column(String)
    postal_code = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    platform_created_at = Column(DateTime)  # When created on the original platform
    
    # Analytics fields (calculated)
    total_spent = Column(Numeric(12, 2), default=0)
    orders_count = Column(Integer, default=0)
    average_order_value = Column(Numeric(10, 2), default=0)
    last_order_date = Column(DateTime)
    
    # Customer status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    orders = relationship("UniversalOrder", back_populates="customer")
    
    def __repr__(self):
        return f"<UniversalCustomer(platform={self.platform}, email={self.email})>"


class UniversalProduct(Base):
    """
    Universal product model for multi-platform product data
    """
    __tablename__ = "universal_products"
    
    # Internal ID
    id = Column(Integer, primary_key=True)
    
    # Platform-specific information
    external_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    
    # Product information
    name = Column(String, nullable=False)
    description = Column(Text)
    sku = Column(String, index=True)
    barcode = Column(String)
    
    # Pricing
    price = Column(Numeric(10, 2))
    cost = Column(Numeric(10, 2))  # Cost of goods sold
    compare_at_price = Column(Numeric(10, 2))  # MSRP or original price
    
    # Categories and organization
    category = Column(String)
    subcategory = Column(String)
    brand = Column(String)
    vendor = Column(String)
    product_type = Column(String)
    tags = Column(Text)  # JSON or comma-separated tags
    
    # Inventory
    inventory_quantity = Column(Integer, default=0)
    track_inventory = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    platform_created_at = Column(DateTime)
    
    # Analytics fields (calculated)
    total_sales = Column(Numeric(12, 2), default=0)
    units_sold = Column(Integer, default=0)
    
    # Relationships
    order_items = relationship("UniversalOrderItem", back_populates="product")
    
    def __repr__(self):
        return f"<UniversalProduct(platform={self.platform}, name={self.name})>"


class UniversalOrder(Base):
    """
    Universal order model for multi-platform order data
    """
    __tablename__ = "universal_orders"
    
    # Internal ID
    id = Column(Integer, primary_key=True)
    
    # Platform-specific information
    external_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    
    # Customer relationship
    customer_id = Column(Integer, ForeignKey("universal_customers.id"))
    customer_external_id = Column(String)  # For easier lookups
    
    # Order details
    order_number = Column(String)  # Human-readable order number
    order_date = Column(DateTime, nullable=False, index=True)
    
    # Financial information
    subtotal = Column(Numeric(10, 2))
    tax_amount = Column(Numeric(10, 2), default=0)
    shipping_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    
    # Order status
    status = Column(String)  # pending, processing, shipped, delivered, cancelled, refunded
    fulfillment_status = Column(String)  # unfulfilled, partial, fulfilled
    payment_status = Column(String)  # pending, paid, partially_paid, refunded, voided
    
    # Shipping information
    shipping_method = Column(String)
    tracking_number = Column(String)
    
    # Contact information (in case customer data is missing)
    email = Column(String)
    phone = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Relationships
    customer = relationship("UniversalCustomer", back_populates="orders")
    items = relationship("UniversalOrderItem", back_populates="order")
    
    def __repr__(self):
        return f"<UniversalOrder(platform={self.platform}, total={self.total_amount})>"


class UniversalOrderItem(Base):
    """
    Universal order item model for multi-platform line item data
    """
    __tablename__ = "universal_order_items"
    
    # Internal ID
    id = Column(Integer, primary_key=True)
    
    # Platform-specific information
    external_id = Column(String)
    platform = Column(String, nullable=False)
    
    # Relationships
    order_id = Column(Integer, ForeignKey("universal_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("universal_products.id"))
    
    # External IDs for easier mapping
    order_external_id = Column(String)
    product_external_id = Column(String)
    
    # Product information (at time of purchase)
    product_name = Column(String)
    product_sku = Column(String)
    variant_title = Column(String)  # Size, Color, etc.
    
    # Quantities and pricing
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Discounts and taxes at line item level
    discount_amount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    
    # Fulfillment
    fulfillment_status = Column(String)  # fulfilled, unfulfilled, partial
    quantity_fulfilled = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = relationship("UniversalOrder", back_populates="items")
    product = relationship("UniversalProduct", back_populates="order_items")
    
    def __repr__(self):
        return f"<UniversalOrderItem(product={self.product_name}, qty={self.quantity})>"


class UniversalCustomerSegment(Base):
    """
    Universal customer segmentation based on universal metrics
    """
    __tablename__ = "universal_customer_segments"
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("universal_customers.id"), nullable=False)
    
    # Segmentation data
    segment = Column(String, nullable=False)  # VIP, Regular, New, At-Risk, etc.
    segment_score = Column(Numeric(5, 2))
    
    # Metrics used for segmentation
    total_orders = Column(Integer)
    total_spent = Column(Numeric(12, 2))
    average_order_value = Column(Numeric(10, 2))
    days_since_last_order = Column(Integer)
    lifetime_value_score = Column(Numeric(5, 2))
    
    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    customer = relationship("UniversalCustomer")
    
    def __repr__(self):
        return f"<UniversalCustomerSegment(segment={self.segment}, score={self.segment_score})>"