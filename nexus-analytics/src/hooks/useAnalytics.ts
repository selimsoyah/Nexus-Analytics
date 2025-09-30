// Universal Analytics Data Fetching Hooks
// React hooks for fetching data from our universal analytics APIs

import { useState, useEffect, useCallback } from 'react';
import {
  Customer,
  Product,
  Order,
  CustomerInsight,
  ProductPerformance,
  CrossPlatformInsight,
  UniversalAnalyticsResponse,
  AnalyticsFilters
} from '@/types/analytics';

// Base API URL - adjust if your backend runs on different port
const API_BASE_URL = 'http://localhost:8000';

// Generic hook for API calls with loading and error states
function useApiCall<T>(url: string, dependencies: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          // Add authorization header if user is logged in
          ...(typeof window !== 'undefined' && localStorage.getItem('token') 
            ? { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
            : {}
          ),
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('API call failed:', err);
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// Hook for universal analytics overview
export function useUniversalAnalytics(filters?: AnalyticsFilters) {
  const queryParams = new URLSearchParams();
  if (filters?.platform) queryParams.append('platform', filters.platform);
  
  const url = `/universal/analytics/overview${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  return useApiCall<UniversalAnalyticsResponse>(url, [filters]);
}

// Hook for universal customers data
export function useUniversalCustomers(filters?: AnalyticsFilters) {
  const queryParams = new URLSearchParams();
  if (filters?.platform) queryParams.append('platform', filters.platform);
  
  const url = `/universal/customers${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  const { data, loading, error, refetch } = useApiCall<{
    customers: Customer[];
    platform_filter: string | null;
    total_count: number;
  }>(url, [filters]);

  return {
    customers: data?.customers || [],
    totalCount: data?.total_count || 0,
    platformFilter: data?.platform_filter,
    loading,
    error,
    refetch
  };
}

// Hook for universal products data
export function useUniversalProducts(filters?: AnalyticsFilters) {
  const queryParams = new URLSearchParams();
  if (filters?.platform) queryParams.append('platform', filters.platform);
  if (filters?.category) queryParams.append('category', filters.category);
  
  const url = `/universal/products${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  const { data, loading, error, refetch } = useApiCall<{
    products: Product[];
    filters: { platform: string | null; category: string | null };
    total_count: number;
  }>(url, [filters]);

  return {
    products: data?.products || [],
    totalCount: data?.total_count || 0,
    appliedFilters: data?.filters,
    loading,
    error,
    refetch
  };
}

// Hook for universal orders data
export function useUniversalOrders(filters?: AnalyticsFilters) {
  const queryParams = new URLSearchParams();
  if (filters?.platform) queryParams.append('platform', filters.platform);
  
  const url = `/universal/orders${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  const { data, loading, error, refetch } = useApiCall<{
    orders: Order[];
    platform_filter: string | null;
    total_count: number;
  }>(url, [filters]);

  return {
    orders: data?.orders || [],
    totalCount: data?.total_count || 0,
    platformFilter: data?.platform_filter,
    loading,
    error,
    refetch
  };
}

// Hook for enhanced customer insights
export function useCustomerInsights(customerExternalId: string) {
  const url = `/v2/analytics/customer-insights/${customerExternalId}`;
  
  return useApiCall<CustomerInsight>(url, [customerExternalId]);
}

// Hook for product performance analytics
export function useProductPerformance(filters?: AnalyticsFilters) {
  const queryParams = new URLSearchParams();
  if (filters?.platform) queryParams.append('platform', filters.platform);
  if (filters?.category) queryParams.append('category', filters.category);
  
  const url = `/v2/analytics/product-performance${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
  
  const { data, loading, error, refetch } = useApiCall<{
    products: ProductPerformance[];
    total_products: number;
    filters_applied: { platform: string | null; category: string | null; limit: number };
  }>(url, [filters]);

  return {
    products: data?.products || [],
    totalProducts: data?.total_products || 0,
    filtersApplied: data?.filters_applied,
    loading,
    error,
    refetch
  };
}

// Hook for cross-platform insights
export function useCrossPlatformInsights() {
  const url = '/v2/analytics/cross-platform-insights';
  
  return useApiCall<CrossPlatformInsight>(url);
}

// Hook for detailed customer segments
export function useCustomerSegments() {
  const url = '/v2/analytics/customer-segments-detailed';
  
  return useApiCall<any>(url); // Define proper type based on your API response
}

// Hook with auto-refresh capabilities
export function useAutoRefresh<T>(
  hookFunction: () => { data: T; loading: boolean; error: string | null; refetch: () => void },
  intervalMs: number = 30000 // 30 seconds default
) {
  const result = hookFunction();
  
  useEffect(() => {
    if (intervalMs <= 0) return;
    
    const interval = setInterval(() => {
      result.refetch();
    }, intervalMs);

    return () => clearInterval(interval);
  }, [result.refetch, intervalMs]);

  return result;
}

// Hook for combined analytics data (for dashboard overview)
export function useDashboardData(filters?: AnalyticsFilters) {
  const analytics = useUniversalAnalytics(filters);
  const customers = useUniversalCustomers(filters);
  const products = useUniversalProducts(filters);
  const orders = useUniversalOrders(filters);
  const productPerformance = useProductPerformance(filters);
  const crossPlatform = useCrossPlatformInsights();

  const loading = analytics.loading || customers.loading || products.loading || 
                  orders.loading || productPerformance.loading || crossPlatform.loading;
  
  const error = analytics.error || customers.error || products.error || 
                orders.error || productPerformance.error || crossPlatform.error;

  const refetchAll = useCallback(() => {
    analytics.refetch();
    customers.refetch();
    products.refetch();
    orders.refetch();
    productPerformance.refetch();
    crossPlatform.refetch();
  }, [analytics.refetch, customers.refetch, products.refetch, orders.refetch, productPerformance.refetch, crossPlatform.refetch]);

  return {
    analytics: analytics.data,
    customers: customers.customers,
    products: products.products,
    orders: orders.orders,
    productPerformance: productPerformance.products,
    crossPlatform: crossPlatform.data,
    loading,
    error,
    refetchAll
  };
}

// Utility hook for managing filters state
export function useAnalyticsFilters(initialFilters?: AnalyticsFilters) {
  const [filters, setFilters] = useState<AnalyticsFilters>(initialFilters || {});

  const updateFilter = useCallback(<K extends keyof AnalyticsFilters>(
    key: K, 
    value: AnalyticsFilters[K]
  ) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({});
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(initialFilters || {});
  }, [initialFilters]);

  return {
    filters,
    setFilters,
    updateFilter,
    clearFilters,
    resetFilters
  };
}