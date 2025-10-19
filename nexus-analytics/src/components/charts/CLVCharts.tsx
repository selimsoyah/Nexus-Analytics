/**
 * Customer Lifetime Value (CLV) Chart Components
 * 
 * These components provide comprehensive CLV visualizations including:
 * - CLV distribution across customers
 * - CLV by customer segments 
 * - Risk analysis and churn predictions
 * - Platform-wise CLV comparisons
 */

'use client';

import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, ScatterChart, Scatter,
  AreaChart, Area, ComposedChart
} from 'recharts';
import { TrendingUp, AlertTriangle, Users, DollarSign, Target, Zap } from 'lucide-react';
import { ChartContainer, formatCurrency, formatNumber, COLORS } from './ChartUtils';

// Types for CLV data
interface CLVMetrics {
  customer_id: string;
  platform: string;
  clv: number;
  confidence_range: {
    low: number;
    high: number;
  };
  risk_score: number;
  risk_level: string;
  segment: string;
  metrics: {
    avg_order_value: number;
    purchase_frequency: number;
    total_orders: number;
    total_spent: number;
    days_since_last_order: number;
  };
}

interface CLVSegment {
  segment: string;
  customer_count: number;
  percentage_of_total: number;
  avg_clv: number;
  total_clv: number;
  avg_risk_score: number;
  retention_insights: {
    at_risk_percentage: number;
    avg_days_since_last_order: number;
    retention_health: string;
  };
  recommendations: string[];
}

interface CLVPlatformSummary {
  platform: string;
  total_customers: number;
  avg_total_spent: number;
  avg_orders: number;
  avg_order_value: number;
  estimated_avg_clv: number;
  at_risk_customers: number;
  one_time_customers: number;
  retention_rate: number;
  clv_health: string;
  recommendations: string[];
}

// CLV Distribution Chart
export const CLVDistributionChart: React.FC<{ data: CLVMetrics[] }> = ({ data }) => {
  // Group customers by CLV ranges
  const distributionData = React.useMemo(() => {
    const ranges = [
      { min: 0, max: 100, label: '$0-$100' },
      { min: 100, max: 500, label: '$100-$500' },
      { min: 500, max: 1000, label: '$500-$1K' },
      { min: 1000, max: 2500, label: '$1K-$2.5K' },
      { min: 2500, max: 5000, label: '$2.5K-$5K' },
      { min: 5000, max: 10000, label: '$5K-$10K' },
      { min: 10000, max: Infinity, label: '$10K+' }
    ];

    return ranges.map(range => {
      const customers = data.filter(d => d.clv >= range.min && d.clv < range.max);
      const totalClv = customers.reduce((sum, c) => sum + c.clv, 0);
      
      return {
        range: range.label,
        customer_count: customers.length,
        total_clv: totalClv,
        avg_clv: customers.length > 0 ? totalClv / customers.length : 0,
        percentage: (customers.length / data.length) * 100
      };
    });
  }, [data]);

  return (
    <ChartContainer
      title="CLV Distribution"
      description="Distribution of customers across CLV ranges"
      icon={<TrendingUp className="h-5 w-5" />}
    >
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={distributionData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="range" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip 
            formatter={(value, name) => [
              name === 'customer_count' ? formatNumber(value as number) : formatCurrency(value as number),
              name === 'customer_count' ? 'Customers' : 'Total CLV'
            ]}
          />
          <Legend />
          <Bar yAxisId="left" dataKey="customer_count" fill={COLORS[0]} name="Customer Count" />
          <Line 
            yAxisId="right" 
            type="monotone" 
            dataKey="total_clv" 
            stroke={COLORS[1]} 
            strokeWidth={3}
            name="Total CLV"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// CLV by Segments Chart
export const CLVSegmentsChart: React.FC<{ data: CLVSegment[] }> = ({ data }) => {
  return (
    <ChartContainer
      title="CLV by Customer Segments"
      description="Average CLV and customer distribution by segment"
      icon={<Users className="h-5 w-5" />}
    >
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="horizontal">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="segment" type="category" width={100} />
          <Tooltip 
            formatter={(value, name) => [
              name === 'customer_count' ? formatNumber(value as number) : formatCurrency(value as number),
              name === 'customer_count' ? 'Customers' : 'Avg CLV'
            ]}
          />
          <Legend />
          <Bar dataKey="avg_clv" fill={COLORS[0]} name="Average CLV" />
          <Bar dataKey="customer_count" fill={COLORS[1]} name="Customer Count" />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// Risk vs CLV Scatter Chart
export const CLVRiskScatterChart: React.FC<{ data: CLVMetrics[] }> = ({ data }) => {
  const scatterData = data.map(customer => ({
    clv: customer.clv,
    risk_score: customer.risk_score * 100, // Convert to percentage
    segment: customer.segment,
    customer_id: customer.customer_id
  }));

  return (
    <ChartContainer
      title="CLV vs Risk Analysis"
      description="Customer positioning by CLV and churn risk"
      icon={<AlertTriangle className="h-5 w-5" />}
    >
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart data={scatterData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="clv" 
            name="CLV" 
            tickFormatter={(value) => formatCurrency(value)}
          />
          <YAxis 
            dataKey="risk_score" 
            name="Risk Score %" 
            domain={[0, 100]}
          />
          <Tooltip 
            cursor={{ strokeDasharray: '3 3' }}
            formatter={(value, name) => [
              name === 'clv' ? formatCurrency(value as number) : `${value}%`,
              name === 'clv' ? 'CLV' : 'Risk Score'
            ]}
            labelFormatter={(value) => `Customer: ${value}`}
          />
          <Scatter dataKey="risk_score" fill={COLORS[0]} />
        </ScatterChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// Platform CLV Comparison
export const PlatformCLVChart: React.FC<{ data: CLVPlatformSummary[] }> = ({ data }) => {
  return (
    <ChartContainer
      title="CLV by Platform"
      description="Platform comparison of customer lifetime value"
      icon={<Target className="h-5 w-5" />}
    >
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="platform" />
          <YAxis />
          <Tooltip 
            formatter={(value) => [formatCurrency(value as number), 'Average CLV']}
          />
          <Legend />
          <Bar dataKey="estimated_avg_clv" fill={COLORS[0]} name="Average CLV" />
        </BarChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// CLV Confidence Intervals Chart
export const CLVConfidenceChart: React.FC<{ data: CLVMetrics[] }> = ({ data }) => {
  // Sort by CLV and take top customers for better visualization
  const topCustomers = data
    .sort((a, b) => b.clv - a.clv)
    .slice(0, 20)
    .map((customer, index) => ({
      customer_rank: index + 1,
      customer_id: customer.customer_id,
      clv: customer.clv,
      confidence_low: customer.confidence_range.low,
      confidence_high: customer.confidence_range.high,
      segment: customer.segment
    }));

  return (
    <ChartContainer
      title="CLV Confidence Intervals (Top 20)"
      description="CLV predictions with confidence ranges for top customers"
      icon={<Zap className="h-5 w-5" />}
    >
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={topCustomers}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="customer_rank" />
          <YAxis tickFormatter={(value) => formatCurrency(value)} />
          <Tooltip 
            formatter={(value) => [formatCurrency(value as number), 'CLV']}
            labelFormatter={(value) => `Customer Rank: ${value}`}
          />
          <Legend />
          <Area 
            dataKey="confidence_high"
            stackId="1"
            stroke={COLORS[2]}
            fill={COLORS[2]}
            fillOpacity={0.3}
            name="Confidence High"
          />
          <Area 
            dataKey="confidence_low"
            stackId="1"
            stroke={COLORS[3]}
            fill={COLORS[3]}
            fillOpacity={0.3}
            name="Confidence Low"
          />
          <Line 
            type="monotone" 
            dataKey="clv" 
            stroke={COLORS[0]} 
            strokeWidth={3}
            name="CLV"
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// CLV Segments Pie Chart
export const CLVSegmentsPieChart: React.FC<{ data: CLVSegment[] }> = ({ data }) => {
  const pieData = data.map((segment, index) => ({
    name: segment.segment,
    value: segment.customer_count,
    percentage: segment.percentage_of_total,
    color: COLORS[index % COLORS.length]
  }));

  return (
    <ChartContainer
      title="Customer Segments Distribution"
      description="Proportion of customers in each CLV segment"
      icon={<Users className="h-5 w-5" />}
    >
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percentage }: any) => `${name}: ${(percentage as number).toFixed(1)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip 
            formatter={(value) => [formatNumber(value as number), 'Customers']}
          />
        </PieChart>
      </ResponsiveContainer>
    </ChartContainer>
  );
};

// Main CLV Analytics Component
export const CLVAnalytics: React.FC<{ filters: any }> = ({ filters }) => {
  const [clvData, setCLVData] = useState<CLVMetrics[]>([]);
  const [segmentsData, setSegmentsData] = useState<CLVSegment[]>([]);
  const [platformData, setPlatformData] = useState<CLVPlatformSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCLVData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Get authentication token
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        if (!token) {
          throw new Error('Authentication required');
        }

        // Build query parameters
        const params = new URLSearchParams();
        if (filters.platform) params.append('platform', filters.platform);
        params.append('limit', '200'); // Get a good sample size
        
        // Base API URL - same as other hooks
        const API_BASE_URL = 'http://localhost:8001';

        // Headers with authentication
        const headers = {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        };

        // Fetch bulk CLV data
        const clvResponse = await fetch(`${API_BASE_URL}/v2/analytics/clv/bulk?${params}`, { headers });
        if (!clvResponse.ok) throw new Error('Failed to fetch CLV data');
        const clvResult = await clvResponse.json();
        setCLVData(clvResult.customers || []);

        // Fetch segments analysis
        const segmentsResponse = await fetch(`${API_BASE_URL}/v2/analytics/clv/segments?${params}`, { headers });
        if (!segmentsResponse.ok) throw new Error('Failed to fetch segments data');
        const segmentsResult = await segmentsResponse.json();
        setSegmentsData(segmentsResult.segments || []);

        // Fetch platform summary
        const platformParams = new URLSearchParams();
        if (filters.platform) platformParams.append('platform', filters.platform);
        
        const platformResponse = await fetch(`${API_BASE_URL}/v2/analytics/clv/platform-summary?${platformParams}`, { headers });
        if (!platformResponse.ok) throw new Error('Failed to fetch platform data');
        const platformResult = await platformResponse.json();
        setPlatformData(platformResult.platform_summaries || []);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch CLV data');
        console.error('CLV data fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchCLVData();
  }, [filters]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white p-6 rounded-lg shadow-sm border animate-pulse">
              <div className="h-6 bg-gray-200 rounded mb-4"></div>
              <div className="h-64 bg-gray-100 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading CLV Data</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  if (clvData.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-yellow-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">No CLV Data Available</h3>
            <div className="mt-2 text-sm text-yellow-700">
              No customers found for CLV analysis. Please check your filters or ensure customer data exists.
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DollarSign className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Average CLV</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {formatCurrency(clvData.reduce((sum, c) => sum + c.clv, 0) / clvData.length)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">High-Risk Customers</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {clvData.filter(c => c.risk_level === 'high').length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Target className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">VIP Customers</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {clvData.filter(c => c.segment === 'VIP').length}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total CLV</dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {formatCurrency(clvData.reduce((sum, c) => sum + c.clv, 0))}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CLVDistributionChart data={clvData} />
        <CLVSegmentsPieChart data={segmentsData} />
        <CLVSegmentsChart data={segmentsData} />
        <CLVRiskScatterChart data={clvData} />
        <CLVConfidenceChart data={clvData} />
        <PlatformCLVChart data={platformData} />
      </div>
    </div>
  );
};