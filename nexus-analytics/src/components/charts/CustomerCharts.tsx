'use client';

// Customer Analytics Charts
// Charts focused on customer data, behavior, and insights

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart
} from 'recharts';
import { TrendingUp, Users, DollarSign, ShoppingCart } from 'lucide-react';
import { useUniversalCustomers, useUniversalOrders } from '@/hooks/useAnalytics';
import {
  CHART_COLORS,
  PLATFORM_COLORS,
  formatCurrency,
  formatNumber,
  currencyTooltipFormatter,
  numberTooltipFormatter,
  CHART_DIMENSIONS,
  CHART_MARGINS,
  cn
} from './ChartUtils';
import { AnalyticsFilters } from '@/types/analytics';

interface CustomerChartsProps {
  filters?: AnalyticsFilters;
}

// Customer Segments Pie Chart
export function CustomerSegmentsPieChart({ filters }: CustomerChartsProps) {
  const { customers, loading, error } = useUniversalCustomers(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading customer segments...</div>
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

  // Segment customers by spending
  const segments = customers.reduce((acc, customer) => {
    const spending = customer.total_spent;
    let segment = 'Low Value';
    
    if (spending > 200) segment = 'High Value';
    else if (spending > 100) segment = 'Medium Value';
    
    acc[segment] = (acc[segment] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const chartData = Object.entries(segments).map(([name, value], index) => ({
    name,
    value,
    color: Object.values(CHART_COLORS)[index]
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <Users className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-semibold">Customer Segments</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${((percent as number) * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={numberTooltipFormatter} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      
      <div className="mt-4 text-sm text-gray-600">
        Total Customers: {formatNumber(customers.length)}
      </div>
    </div>
  );
}

// Top Customers Bar Chart
export function TopCustomersBarChart({ filters }: CustomerChartsProps) {
  const { customers, loading, error } = useUniversalCustomers(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading top customers...</div>
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

  // Get top 10 customers by spending
  const topCustomers = customers
    .sort((a, b) => b.total_spent - a.total_spent)
    .slice(0, 10)
    .map(customer => ({
      name: customer.full_name || `${customer.first_name} ${customer.last_name}`,
      value: customer.total_spent,
      orders: customer.orders_count,
      platform: customer.platform
    }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="h-5 w-5 text-green-600" />
        <h3 className="text-lg font-semibold">Top Customers by Spending</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={topCustomers}
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
            labelFormatter={(label) => `Customer: ${label}`}
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border rounded-lg shadow-lg">
                    <p className="font-semibold">{label}</p>
                    <p className="text-green-600">Spent: {formatCurrency(data.value)}</p>
                    <p className="text-blue-600">Orders: {data.orders}</p>
                    <p className="text-gray-600">Platform: {data.platform}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Bar 
            dataKey="value" 
            fill={CHART_COLORS.primary}
            name="Total Spent"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// Customer Growth Over Time (using order dates as proxy)
export function CustomerGrowthChart({ filters }: CustomerChartsProps) {
  const { orders, loading, error } = useUniversalOrders(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading customer growth...</div>
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

  // Group orders by date to show activity over time
  const ordersByDate = orders.reduce((acc, order) => {
    const date = order.order_date.split('T')[0]; // Get date part only
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
        <ShoppingCart className="h-5 w-5 text-purple-600" />
        <h3 className="text-lg font-semibold">Order Activity Over Time</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
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
          <Area
            type="monotone"
            dataKey="orders"
            stroke={CHART_COLORS.purple}
            fill={CHART_COLORS.purple}
            fillOpacity={0.3}
            name="Orders"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// Customer Platform Distribution
export function CustomerPlatformChart({ filters }: CustomerChartsProps) {
  const { customers, loading, error } = useUniversalCustomers(filters);

  if (loading) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-50 rounded-lg">
        <div className="text-gray-500">Loading platform distribution...</div>
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

  // Group customers by platform
  const platformData = customers.reduce((acc, customer) => {
    const platform = customer.platform;
    acc[platform] = (acc[platform] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const chartData = Object.entries(platformData).map(([platform, count]) => ({
    name: platform.replace('_', ' ').toUpperCase(),
    value: count,
    color: PLATFORM_COLORS[platform as keyof typeof PLATFORM_COLORS] || CHART_COLORS.primary
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center gap-2 mb-4">
        <DollarSign className="h-5 w-5 text-orange-600" />
        <h3 className="text-lg font-semibold">Customers by Platform</h3>
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
    </div>
  );
}

// Combined Customer Analytics Component
export function CustomerAnalytics({ filters }: CustomerChartsProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CustomerSegmentsPieChart filters={filters} />
        <CustomerPlatformChart filters={filters} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TopCustomersBarChart filters={filters} />
        <CustomerGrowthChart filters={filters} />
      </div>
    </div>
  );
}