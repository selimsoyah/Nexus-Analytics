'use client';

// Product Performance Charts
// Charts focused on product data, sales performance, and revenue insights

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  ScatterChart,
  Scatter
} from 'recharts';
import { Package, TrendingUp, ShoppingBag, Target } from 'lucide-react';
import { useProductPerformance, useUniversalProducts } from '@/hooks/useAnalytics';
import {
  CHART_COLORS,
  PLATFORM_COLORS,
  formatCurrency,
  formatNumber,
  currencyTooltipFormatter,
  numberTooltipFormatter,
  CHART_DIMENSIONS,
  CHART_MARGINS
} from './ChartUtils';
import { AnalyticsFilters } from '@/types/analytics';

interface ProductChartsProps {
  filters?: AnalyticsFilters;
}

// Product Revenue Bar Chart
export function ProductRevenueChart({ filters }: ProductChartsProps) {
  const { products, loading, error } = useProductPerformance(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading product revenue...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-red-50 rounded-lg">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  // Get top 10 products by revenue
  const topProducts = products
    .sort((a, b) => b.total_revenue - a.total_revenue)
    .slice(0, 10)
    .map(product => ({
      name: product.name,
      revenue: product.total_revenue,
      units_sold: product.total_units_sold,
      price: product.list_price,
      platform: product.platform
    }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-5 w-5 text-green-600" />
        <h3 className="text-lg font-semibold">Product Revenue Performance</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={topProducts}
          margin={CHART_MARGINS.withLabels}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="name" 
            angle={-45}
            textAnchor="end"
            height={100}
            fontSize={12}
          />
          <YAxis />
          <Tooltip 
            formatter={currencyTooltipFormatter}
            labelFormatter={(label) => `Product: ${label}`}
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border rounded-lg shadow-lg">
                    <p className="font-semibold">{label}</p>
                    <p className="text-green-600">Revenue: {formatCurrency(data.revenue)}</p>
                    <p className="text-blue-600">Units Sold: {formatNumber(data.units_sold)}</p>
                    <p className="text-purple-600">Price: {formatCurrency(data.price)}</p>
                    <p className="text-gray-600">Platform: {data.platform}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Bar 
            dataKey="revenue" 
            fill={CHART_COLORS.secondary}
            name="Revenue"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// Product Units Sold Horizontal Bar Chart
export function ProductVolumeChart({ filters }: ProductChartsProps) {
  const { products, loading, error } = useProductPerformance(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading product volume...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-red-50 rounded-lg">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  // Get top 10 products by units sold
  const topProducts = products
    .sort((a, b) => b.total_units_sold - a.total_units_sold)
    .slice(0, 10)
    .map(product => ({
      name: product.name,
      units: product.total_units_sold,
      revenue: product.total_revenue,
      customers: product.unique_customers
    }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <Package className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-semibold">Product Sales Volume</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={topProducts}
          layout="horizontal"
          margin={{ ...CHART_MARGINS.withLabels, left: 80 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis 
            dataKey="name" 
            type="category"
            width={80}
            fontSize={12}
          />
          <Tooltip 
            formatter={numberTooltipFormatter}
            labelFormatter={(label) => `Product: ${label}`}
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border rounded-lg shadow-lg">
                    <p className="font-semibold">{label}</p>
                    <p className="text-blue-600">Units Sold: {formatNumber(data.units)}</p>
                    <p className="text-green-600">Revenue: {formatCurrency(data.revenue)}</p>
                    <p className="text-purple-600">Customers: {formatNumber(data.customers)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Bar 
            dataKey="units" 
            fill={CHART_COLORS.primary}
            name="Units Sold"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// Product Category Distribution Pie Chart
export function ProductCategoryChart({ filters }: ProductChartsProps) {
  const { products, loading, error } = useUniversalProducts(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading category distribution...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-red-50 rounded-lg">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  // Group products by category
  const categoryData = products.reduce((acc, product) => {
    const category = product.category || 'Uncategorized';
    acc[category] = (acc[category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const chartData = Object.entries(categoryData).map(([category, count], index) => ({
    name: category,
    value: count,
    color: Object.values(CHART_COLORS)[index % Object.values(CHART_COLORS).length]
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <ShoppingBag className="h-5 w-5 text-purple-600" />
        <h3 className="text-lg font-semibold">Products by Category</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value, percent }) => 
              `${name}: ${value} (${((percent as number) * 100).toFixed(0)}%)`
            }
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={numberTooltipFormatter} />
        </PieChart>
      </ResponsiveContainer>
      
      <div className="mt-4 text-sm text-gray-600">
        Total Products: {formatNumber(products.length)}
      </div>
    </div>
  );
}

// Price vs Sales Performance Scatter Chart
export function PricePerformanceChart({ filters }: ProductChartsProps) {
  const { products, loading, error } = useProductPerformance(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading price performance...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-red-50 rounded-lg">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  const chartData = products.map(product => ({
    name: product.name,
    price: product.list_price,
    sales: product.total_units_sold,
    revenue: product.total_revenue,
    platform: product.platform
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <Target className="h-5 w-5 text-orange-600" />
        <h3 className="text-lg font-semibold">Price vs Sales Performance</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart
          data={chartData}
          margin={CHART_MARGINS.withLabels}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            type="number" 
            dataKey="price"
            name="Price"
            tickFormatter={(value) => `$${value}`}
          />
          <YAxis 
            type="number" 
            dataKey="sales"
            name="Units Sold"
          />
          <Tooltip 
            cursor={{ strokeDasharray: '3 3' }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border rounded-lg shadow-lg">
                    <p className="font-semibold">{data.name}</p>
                    <p className="text-green-600">Price: {formatCurrency(data.price)}</p>
                    <p className="text-blue-600">Units Sold: {formatNumber(data.sales)}</p>
                    <p className="text-purple-600">Revenue: {formatCurrency(data.revenue)}</p>
                    <p className="text-gray-600">Platform: {data.platform}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter 
            name="Products" 
            dataKey="sales" 
            fill={CHART_COLORS.accent}
          />
        </ScatterChart>
      </ResponsiveContainer>
      
      <div className="mt-4 text-sm text-gray-600">
        Each dot represents a product. X-axis shows price, Y-axis shows units sold.
      </div>
    </div>
  );
}

// Combined Product Analytics Component
export function ProductAnalytics({ filters }: ProductChartsProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ProductRevenueChart filters={filters} />
        <ProductVolumeChart filters={filters} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ProductCategoryChart filters={filters} />
        <PricePerformanceChart filters={filters} />
      </div>
    </div>
  );
}