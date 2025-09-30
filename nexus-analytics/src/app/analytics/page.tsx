'use client';

// Analytics Dashboard Page
// Main analytics dashboard with comprehensive data visualizations

import React, { useState, useCallback } from 'react';
import { DollarSign, Users, Package, ShoppingCart } from 'lucide-react';
import ProtectedRoute from '@/app/protectedRoute';
import { DashboardLayout, MetricCard, LoadingSpinner, ErrorMessage } from '@/components/dashboard/DashboardLayout';
import { CustomerAnalytics } from '@/components/charts/CustomerCharts';
import { ProductAnalytics } from '@/components/charts/ProductCharts';
import { SalesAnalytics } from '@/components/charts/SalesCharts';
import { CLVAnalytics } from '@/components/charts/CLVCharts';
import { useDashboardData, useAnalyticsFilters, useAutoRefresh } from '@/hooks/useAnalytics';
import { formatCurrency, formatNumber } from '@/components/charts/ChartUtils';

type DashboardTab = 'overview' | 'customers' | 'products' | 'sales' | 'clv';

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  // Filters management
  const { filters, updateFilter, clearFilters } = useAnalyticsFilters();
  
  // Data fetching with auto-refresh
  const dashboardData = useDashboardData(filters);

  const { 
    analytics, 
    customers, 
    products, 
    orders, 
    productPerformance,
    crossPlatform,
    loading, 
    error, 
    refetchAll 
  } = dashboardData;

  const handleRefresh = useCallback(() => {
    refetchAll();
    setLastUpdated(new Date());
  }, [refetchAll]);

  const handleFiltersChange = useCallback((newFilters: any) => {
    Object.entries(newFilters).forEach(([key, value]) => {
      updateFilter(key as any, value);
    });
  }, [updateFilter]);

  // Calculate summary metrics
  const summaryMetrics = React.useMemo(() => {
    if (!analytics || !customers || !orders || !products) {
      return {
        totalRevenue: 0,
        totalCustomers: 0,
        totalOrders: 0,
        totalProducts: 0,
        avgOrderValue: 0
      };
    }

    const totalRevenue = orders.reduce((sum: number, order: any) => sum + order.total_amount, 0);
    const avgOrderValue = orders.length > 0 ? totalRevenue / orders.length : 0;

    return {
      totalRevenue,
      totalCustomers: customers.length,
      totalOrders: orders.length,
      totalProducts: products.length,
      avgOrderValue
    };
  }, [analytics, customers, orders, products]);

  if (loading && !analytics) {
    return (
      <ProtectedRoute>
        <DashboardLayout
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onRefresh={handleRefresh}
          lastUpdated={lastUpdated}
          loading={loading}
        >
          <LoadingSpinner />
        </DashboardLayout>
      </ProtectedRoute>
    );
  }

  if (error) {
    return (
      <ProtectedRoute>
        <DashboardLayout
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onRefresh={handleRefresh}
          lastUpdated={lastUpdated}
          loading={loading}
        >
          <ErrorMessage message={error} />
        </DashboardLayout>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
              </div>
              
              <div className="flex items-center space-x-4">
                <select
                  value={filters.platform || 'all'}
                  onChange={(e) => handleFiltersChange({ 
                    ...filters, 
                    platform: e.target.value === 'all' ? undefined : e.target.value 
                  })}
                  className="block w-40 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                >
                  <option value="all">All Platforms</option>
                  <option value="generic_csv">Generic CSV</option>
                  <option value="shopify">Shopify</option>
                  <option value="woocommerce">WooCommerce</option>
                  <option value="magento">Magento</option>
                </select>
                
                <button
                  onClick={handleRefresh}
                  disabled={loading}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  <ShoppingCart className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              {[
                { id: 'overview', name: 'Overview', icon: DollarSign },
                { id: 'customers', name: 'Customers', icon: Users },
                { id: 'products', name: 'Products', icon: Package },
                { id: 'sales', name: 'Sales', icon: ShoppingCart },
                { id: 'clv', name: 'Customer CLV', icon: DollarSign },
              ].map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as DashboardTab)}
                    className={`${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    } group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm`}
                  >
                    <Icon className="h-5 w-5 mr-2" />
                    {tab.name}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {lastUpdated && (
            <div className="mb-6 text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleString()}
            </div>
          )}

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Summary Metrics */}
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
                <MetricCard
                  title="Total Revenue"
                  value={formatCurrency(summaryMetrics.totalRevenue)}
                  icon={DollarSign}
                  loading={loading}
                />
                <MetricCard
                  title="Total Customers"
                  value={summaryMetrics.totalCustomers}
                  icon={Users}
                  loading={loading}
                />
                <MetricCard
                  title="Total Orders"
                  value={summaryMetrics.totalOrders}
                  icon={ShoppingCart}
                  loading={loading}
                />
                <MetricCard
                  title="Avg Order Value"
                  value={formatCurrency(summaryMetrics.avgOrderValue)}
                  icon={Package}
                  loading={loading}
                />
              </div>

              {/* Overview Charts */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Quick Customer Insights */}
                <div className="bg-white p-6 rounded-lg shadow-sm border">
                  <h3 className="text-lg font-semibold mb-4">Quick Insights</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Active Platforms:</span>
                      <span className="font-medium">
                        {customers ? [...new Set(customers.map((c: any) => c.platform))].length : 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Product Categories:</span>
                      <span className="font-medium">
                        {products ? [...new Set(products.map((p: any) => p.category))].length : 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Latest Order:</span>
                      <span className="font-medium">
                        {orders && orders.length > 0 
                          ? new Date(orders[0].order_date).toLocaleDateString()
                          : 'N/A'
                        }
                      </span>
                    </div>
                  </div>
                </div>

                {/* Platform Distribution */}
                <div className="bg-white p-6 rounded-lg shadow-sm border">
                  <h3 className="text-lg font-semibold mb-4">Platform Distribution</h3>
                  {customers && customers.length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(
                        customers.reduce((acc: Record<string, number>, customer: any) => {
                          acc[customer.platform] = (acc[customer.platform] || 0) + 1;
                          return acc;
                        }, {} as Record<string, number>)
                      ).map(([platform, count]) => (
                        <div key={platform} className="flex justify-between">
                          <span className="text-gray-600 capitalize">
                            {platform.replace('_', ' ')}:
                          </span>
                          <span className="font-medium">{count as number} customers</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-500">No customer data available</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Customers Tab */}
          {activeTab === 'customers' && (
            <CustomerAnalytics filters={filters} />
          )}

          {/* Products Tab */}
          {activeTab === 'products' && (
            <ProductAnalytics filters={filters} />
          )}

          {/* Sales Tab */}
          {activeTab === 'sales' && (
            <SalesAnalytics filters={filters} />
          )}

          {/* CLV Tab */}
          {activeTab === 'clv' && (
            <CLVAnalytics filters={filters} />
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}