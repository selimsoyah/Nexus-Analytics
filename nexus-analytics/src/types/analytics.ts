// Analytics Data Types
// These interfaces match the data structure from our universal analytics APIs

export interface Customer {
  id: number;
  external_id: string;
  platform: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  total_spent: number;
  orders_count: number;
  average_order_value: number;
  last_order_date: string;
  is_active: boolean;
}

export interface Product {
  id: number;
  external_id: string;
  platform: string;
  name: string;
  sku: string;
  price: number;
  category: string;
  inventory_quantity: number;
  is_active: boolean;
  total_sales: number;
  units_sold: number;
}

export interface Order {
  id: number;
  external_id: string;
  platform: string;
  customer_id: number;
  customer_external_id: string;
  order_number: string;
  order_date: string;
  total_amount: number;
  currency: string;
  status: string;
  customer_name: string;
  customer_email: string;
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  total_price: number;
  product_name: string;
  product_sku: string;
}

// Enhanced Analytics Types (from /v2 endpoints)
export interface CustomerInsight {
  customer_id: string;
  name: string;
  email: string;
  platform: string;
  total_spent: number;
  orders_count: number;
  average_order_value: number;
  last_order_date: string;
  orders: OrderDetail[];
}

export interface OrderDetail {
  order_id: string;
  order_date: string;
  total_amount: number;
  status: string;
  products: ProductDetail[];
}

export interface ProductDetail {
  name: string;
  category: string;
  list_price: number;
  sku: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

export interface ProductPerformance {
  name: string;
  category: string;
  list_price: number;
  sku: string;
  platform: string;
  times_purchased: number;
  total_units_sold: number;
  total_revenue: number;
  avg_selling_price: number;
  lowest_selling_price: number;
  highest_selling_price: number;
  unique_customers: number;
  unique_orders: number;
  first_sale_date: string;
  last_sale_date: string;
  discount_rate: number;
  repeat_purchase_rate: number;
}

export interface CrossPlatformInsight {
  platform_overview: PlatformOverview[];
  top_products_cross_platform: TopProduct[];
  category_performance: CategoryPerformance[];
}

export interface PlatformOverview {
  platform: string;
  customers: number;
  orders: number;
  products: number;
  revenue: number;
  avg_order_value: number;
}

export interface TopProduct {
  name: string;
  platform: string;
  category: string;
  units_sold: number;
  revenue: number;
  unique_customers: number;
}

export interface CategoryPerformance {
  category: string;
  platform: string;
  product_count: number;
  units_sold: number;
  revenue: number;
}

// Chart Data Types
export interface ChartDataPoint {
  name: string;
  value: number;
  color?: string;
  platform?: string;
}

export interface TimeSeriesDataPoint {
  date: string;
  value: number;
  platform?: string;
}

export interface ComparisonDataPoint {
  name: string;
  current: number;
  previous?: number;
  platform?: string;
}

// API Response Types
export interface UniversalAnalyticsResponse {
  platform_summary: Array<{
    platform: string;
    total_customers: number;
    avg_customer_value: number;
  }>;
  product_performance: Array<{
    platform: string;
    total_products: number;
    avg_product_price: number;
    total_sales: number;
  }>;
  order_analytics: Array<{
    platform: string;
    total_orders: number;
    total_revenue: number;
    avg_order_value: number;
  }>;
  recent_activity: Array<{
    platform: string;
    order_date: string;
    total_amount: number;
    customer_name: string;
  }>;
  timestamp: string;
}

// Filter and UI Types
export interface AnalyticsFilters {
  platform?: string;
  dateRange?: {
    start: string;
    end: string;
  };
  category?: string;
}

export interface ChartProps {
  data: any[];
  loading?: boolean;
  error?: string | null;
  filters?: AnalyticsFilters;
  onFilterChange?: (filters: AnalyticsFilters) => void;
}