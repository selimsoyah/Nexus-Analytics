'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell
} from 'recharts';

interface PlatformPerformance {
  platform: string;
  total_customers: number;
  total_orders: number;
  total_revenue: number;
  avg_order_value: number;
  avg_customer_value: number;
  customer_retention_rate: number;
  order_frequency: number;
  growth_rate: number;
  market_share: number;
  performance_score: number;
}

interface CrossPlatformSummary {
  total_revenue: number;
  total_customers: number;
  total_orders: number;
  avg_cross_platform_clv: number;
  avg_cross_platform_aov: number;
  platforms_analyzed: number;
}

interface Recommendation {
  type: string;
  priority: string;
  recommendation: string;
  details?: string;
  potential_impact?: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const CrossPlatformAnalytics: React.FC = () => {
  const [performance, setPerformance] = useState<PlatformPerformance[]>([]);
  const [summary, setSummary] = useState<CrossPlatformSummary | null>(null);
  const [recommendations, setRecommendations] = useState<{
    platform_specific_recommendations: Recommendation[];
    global_recommendations: Recommendation[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Check authentication and admin status
        const token = localStorage.getItem('auth_token');
        const userRole = localStorage.getItem('user_role');
        
        if (!token) {
          setAuthError('Please log in to access this page');
          router.push('/login');
          return;
        }
        
        if (userRole !== 'admin') {
          setAuthError('Admin access required for cross-platform analytics');
          setTimeout(() => router.push('/segmentation'), 2000);
          return;
        }
        
        const headers = {
          'Authorization': `Bearer ${token}`
        };
        
        const [performanceRes, kpisRes, recommendationsRes] = await Promise.all([
          fetch('http://localhost:8001/v2/analytics/cross-platform/performance', { headers }),
          fetch('http://localhost:8001/v2/analytics/cross-platform/kpis', { headers }),
          fetch('http://localhost:8001/v2/analytics/cross-platform/recommendations', { headers })
        ]);

        if (performanceRes.status === 403 || kpisRes.status === 403 || recommendationsRes.status === 403) {
          setAuthError('Admin access required for cross-platform analytics');
          setTimeout(() => router.push('/login'), 2000);
          return;
        }
        
        if (!performanceRes.ok || !kpisRes.ok || !recommendationsRes.ok) {
          throw new Error('Failed to fetch cross-platform analytics data');
        }

        const [performanceData, kpisData, recommendationsData] = await Promise.all([
          performanceRes.json(),
          kpisRes.json(),
          recommendationsRes.json()
        ]);

        setPerformance(performanceData.platforms);
        setSummary(kpisData.cross_platform_summary);
        setRecommendations(recommendationsData.recommendations);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number) => {
    return new Intl.NumberFormat('en-US').format(Math.round(value));
  };

  if (authError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="text-red-500 text-xl mb-4">🔒 {authError}</div>
        <div className="text-gray-600">Redirecting...</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading cross-platform analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cross-Platform Analytics</h1>
          <p className="text-gray-600">
            Comprehensive performance analysis across all e-commerce platforms
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="bg-white p-6 rounded-lg shadow border">
            <div className="text-sm font-medium text-gray-600">Total Revenue</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(summary.total_revenue)}
            </div>
            <p className="text-xs text-gray-500">
              Across {summary.platforms_analyzed} platforms
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border">
            <div className="text-sm font-medium text-gray-600">Total Customers</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatNumber(summary.total_customers)}
            </div>
            <p className="text-xs text-gray-500">
              Active across all platforms
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border">
            <div className="text-sm font-medium text-gray-600">Avg Customer Value</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(summary.avg_cross_platform_clv)}
            </div>
            <p className="text-xs text-gray-500">
              Cross-platform average
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow border">
            <div className="text-sm font-medium text-gray-600">Avg Order Value</div>
            <div className="text-2xl font-bold text-gray-900">
              {formatCurrency(summary.avg_cross_platform_aov)}
            </div>
            <p className="text-xs text-gray-500">
              Across all orders
            </p>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold mb-4">Revenue by Platform</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performance as any}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="platform" />
              <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
              <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Revenue']} />
              <Bar dataKey="total_revenue" fill="#0088FE" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-6 rounded-lg shadow border">
          <h3 className="text-lg font-semibold mb-4">Market Share Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={performance as any}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry: any) => `${entry.platform}: ${entry.market_share.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="market_share"
              >
                {performance.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Scores */}
      <div className="bg-white p-6 rounded-lg shadow border">
        <h3 className="text-lg font-semibold mb-4">Platform Performance Scores</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={performance as any} layout="horizontal">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 100]} />
            <YAxis dataKey="platform" type="category" width={100} />
            <Tooltip 
              formatter={(value) => [Number(value).toFixed(1), 'Performance Score']}
              labelFormatter={(label) => `Platform: ${label}`}
            />
            <Bar dataKey="performance_score" fill="#00C49F" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed Metrics Table */}
      <div className="bg-white p-6 rounded-lg shadow border">
        <h3 className="text-lg font-semibold mb-4">Platform Metrics Comparison</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left p-3">Platform</th>
                <th className="text-right p-3">Customers</th>
                <th className="text-right p-3">Orders</th>
                <th className="text-right p-3">Revenue</th>
                <th className="text-right p-3">AOV</th>
                <th className="text-right p-3">CLV</th>
                <th className="text-right p-3">Retention</th>
                <th className="text-right p-3">Growth</th>
              </tr>
            </thead>
            <tbody>
              {performance.map((platform, index) => (
                <tr key={platform.platform} className="border-b hover:bg-gray-50">
                  <td className="p-3 font-medium capitalize">{platform.platform}</td>
                  <td className="text-right p-3">{formatNumber(platform.total_customers)}</td>
                  <td className="text-right p-3">{formatNumber(platform.total_orders)}</td>
                  <td className="text-right p-3">{formatCurrency(platform.total_revenue)}</td>
                  <td className="text-right p-3">{formatCurrency(platform.avg_order_value)}</td>
                  <td className="text-right p-3">{formatCurrency(platform.avg_customer_value)}</td>
                  <td className="text-right p-3">{platform.customer_retention_rate.toFixed(1)}%</td>
                  <td className="text-right p-3">
                    <span className={platform.growth_rate > 0 ? 'text-green-600' : 'text-red-600'}>
                      {platform.growth_rate > 0 ? '+' : ''}{platform.growth_rate.toFixed(1)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recommendations */}
      {recommendations && (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="bg-white p-6 rounded-lg shadow border">
            <h3 className="text-lg font-semibold mb-4">Strategic Recommendations</h3>
            <div className="space-y-4">
              {recommendations.global_recommendations.map((rec, index) => (
                <div key={index} className="p-4 border rounded-lg bg-blue-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                      rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {rec.priority} priority
                    </span>
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                      {rec.type}
                    </span>
                  </div>
                  <p className="text-sm font-medium mb-1">{rec.recommendation}</p>
                  {rec.details && (
                    <p className="text-xs text-gray-600">{rec.details}</p>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow border">
            <h3 className="text-lg font-semibold mb-4">Platform-Specific Actions</h3>
            <div className="space-y-4">
              {recommendations.platform_specific_recommendations.slice(0, 4).map((rec, index) => (
                <div key={index} className="p-4 border rounded-lg bg-green-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                      rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {rec.priority} priority
                    </span>
                    <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                      {rec.type}
                    </span>
                  </div>
                  <p className="text-sm font-medium mb-1">{rec.recommendation}</p>
                  {rec.potential_impact && (
                    <p className="text-xs text-green-600">{rec.potential_impact}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CrossPlatformAnalytics;