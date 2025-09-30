'use client';

// Sales & Revenue Charts
// Charts focused on sales trends, revenue analytics, and business performance over time

import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  ComposedChart
} from 'recharts';
import { DollarSign, TrendingUp, Calendar, BarChart3 } from 'lucide-react';
import { useUniversalOrders, useUniversalAnalytics } from '@/hooks/useAnalytics';
import {
  CHART_COLORS,
  formatCurrency,
  formatNumber,
  formatDate,
  currencyTooltipFormatter,
  numberTooltipFormatter,
  CHART_DIMENSIONS,
  CHART_MARGINS
} from './ChartUtils';
import { AnalyticsFilters } from '@/types/analytics';

interface SalesChartsProps {
  filters?: AnalyticsFilters;
}

// Revenue Trend Line Chart
export function RevenueTrendChart({ filters }: SalesChartsProps) {
  const { orders, loading, error } = useUniversalOrders(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading revenue trends...</div>
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

  // Group orders by date and calculate daily revenue
  const revenueByDate = orders.reduce((acc, order) => {
    const date = order.order_date.split('T')[0]; // Get date part only
    acc[date] = (acc[date] || 0) + order.total_amount;
    return acc;
  }, {} as Record<string, number>);

  const chartData = Object.entries(revenueByDate)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, revenue]) => ({
      date,
      revenue,
      formattedDate: new Date(date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      })
    }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-5 w-5 text-green-600" />
        <h3 className="text-lg font-semibold">Revenue Trend Over Time</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData} margin={CHART_MARGINS.default}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="formattedDate"
            fontSize={12}
          />
          <YAxis 
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip 
            formatter={currencyTooltipFormatter}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="revenue"
            stroke={CHART_COLORS.secondary}
            strokeWidth={3}
            dot={{ fill: CHART_COLORS.secondary, strokeWidth: 2, r: 4 }}
            name="Daily Revenue"
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div className="mt-4 text-sm text-gray-600">
        Total Revenue: {formatCurrency(chartData.reduce((sum, item) => sum + item.revenue, 0))}
      </div>
    </div>
  );
}

// Order Volume Area Chart
export function OrderVolumeChart({ filters }: SalesChartsProps) {
  const { orders, loading, error } = useUniversalOrders(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading order volume...</div>
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

  // Group orders by date
  const ordersByDate = orders.reduce((acc, order) => {
    const date = order.order_date.split('T')[0];
    acc[date] = (acc[date] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const chartData = Object.entries(ordersByDate)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({
      date,
      orders: count,
      formattedDate: new Date(date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      })
    }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-semibold">Order Volume Over Time</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={chartData} margin={CHART_MARGINS.default}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="formattedDate"
            fontSize={12}
          />
          <YAxis />
          <Tooltip 
            formatter={numberTooltipFormatter}
            labelFormatter={(label) => `Date: ${label}`}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="orders"
            stroke={CHART_COLORS.primary}
            fill={CHART_COLORS.primary}
            fillOpacity={0.6}
            name="Orders"
          />
        </AreaChart>
      </ResponsiveContainer>
      
      <div className="mt-4 text-sm text-gray-600">
        Total Orders: {formatNumber(orders.length)}
      </div>
    </div>
  );
}

// Average Order Value Chart
export function AverageOrderValueChart({ filters }: SalesChartsProps) {
  const { orders, loading, error } = useUniversalOrders(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading average order value...</div>
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

  // Calculate AOV by date
  const aovByDate = orders.reduce((acc, order) => {
    const date = order.order_date.split('T')[0];
    if (!acc[date]) {
      acc[date] = { total: 0, count: 0 };
    }
    acc[date].total += order.total_amount;
    acc[date].count += 1;
    return acc;
  }, {} as Record<string, { total: number; count: number }>);

  const chartData = Object.entries(aovByDate)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, { total, count }]) => ({
      date,
      aov: total / count,
      orders: count,
      formattedDate: new Date(date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      })
    }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <DollarSign className="h-5 w-5 text-purple-600" />
        <h3 className="text-lg font-semibold">Average Order Value Trend</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={chartData} margin={CHART_MARGINS.default}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="formattedDate"
            fontSize={12}
          />
          <YAxis 
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <Tooltip 
            formatter={(value, name) => [formatCurrency(value as number), name]}
            labelFormatter={(label) => `Date: ${label}`}
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border rounded-lg shadow-lg">
                    <p className="font-semibold">{label}</p>
                    <p className="text-purple-600">AOV: {formatCurrency(data.aov)}</p>
                    <p className="text-blue-600">Orders: {formatNumber(data.orders)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="aov"
            stroke={CHART_COLORS.purple}
            strokeWidth={3}
            dot={{ fill: CHART_COLORS.purple, strokeWidth: 2, r: 4 }}
            name="Average Order Value"
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div className="mt-4 text-sm text-gray-600">
        Overall AOV: {formatCurrency(orders.reduce((sum, order) => sum + order.total_amount, 0) / orders.length || 0)}
      </div>
    </div>
  );
}

// Sales Performance by Platform
export function SalesByPlatformChart({ filters }: SalesChartsProps) {
  const { orders, loading, error } = useUniversalOrders(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading platform sales...</div>
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

  // Group by platform
  const platformData = orders.reduce((acc, order) => {
    const platform = order.platform;
    if (!acc[platform]) {
      acc[platform] = { revenue: 0, orders: 0 };
    }
    acc[platform].revenue += order.total_amount;
    acc[platform].orders += 1;
    return acc;
  }, {} as Record<string, { revenue: number; orders: number }>);

  const chartData = Object.entries(platformData).map(([platform, data]) => ({
    platform: platform.replace('_', ' ').toUpperCase(),
    revenue: data.revenue,
    orders: data.orders,
    aov: data.revenue / data.orders
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <Calendar className="h-5 w-5 text-orange-600" />
        <h3 className="text-lg font-semibold">Sales Performance by Platform</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={chartData} margin={CHART_MARGINS.withLabels}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="platform" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip 
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border rounded-lg shadow-lg">
                    <p className="font-semibold">{label}</p>
                    <p className="text-green-600">Revenue: {formatCurrency(data.revenue)}</p>
                    <p className="text-blue-600">Orders: {formatNumber(data.orders)}</p>
                    <p className="text-purple-600">AOV: {formatCurrency(data.aov)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Bar 
            yAxisId="left"
            dataKey="revenue" 
            fill={CHART_COLORS.secondary}
            name="Revenue"
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="aov" 
            stroke={CHART_COLORS.accent}
            strokeWidth={3}
            name="AOV"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// Combined Sales Analytics Component
export function SalesAnalytics({ filters }: SalesChartsProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RevenueTrendChart filters={filters} />
        <OrderVolumeChart filters={filters} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AverageOrderValueChart filters={filters} />
        <SalesByPlatformChart filters={filters} />
      </div>
    </div>
  );
}