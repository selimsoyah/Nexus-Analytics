'use client';

import React, { useState, useEffect } from 'react';
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

interface CrossPlatformOverview {
  platform_overview: Array<{
    platform: string;
    total_customers: number;
    total_revenue: number;
    avg_customer_value: number;
    active_customers: number;
    avg_orders_per_customer: number;
  }>;
  order_analytics: Array<{
    platform: string;
    total_orders: number;
    avg_order_value: number;
    platform_revenue: number;
    unique_customers: number;
    completed_orders: number;
    avg_recency_days: number;
  }>;
  product_performance: Array<{
    platform: string;
    total_products: number;
    avg_product_price: number;
    total_sales_items: number;
    product_revenue: number;
  }>;
}

interface PlatformKPIs {
  platform_kpis: Array<{
    platform: string;
    revenue_kpis: {
      total_revenue: number;
      avg_customer_value: number;
      avg_order_value: number;
    };
    customer_kpis: {
      total_customers: number;
      active_customers: number;
      customer_activation_rate: number;
      avg_orders_per_customer: number;
    };
    operational_kpis: {
      total_orders: number;
      completed_orders: number;
      order_completion_rate: number;
      avg_recency_days: number;
    };
  }>;
  cross_platform_summary: {
    total_revenue: number;
    total_customers: number;
    total_orders: number;
    avg_cross_platform_clv: number;
    avg_cross_platform_aov: number;
    platforms_analyzed: number;
  };
}

interface Recommendation {
  type: string;
  priority: string;
  recommendation: string;
  details?: string;
  current_aov?: number;
  potential_impact?: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const CrossPlatformDashboard: React.FC = () => {
  const [overview, setOverview] = useState<CrossPlatformOverview | null>(null);
  const [performance, setPerformance] = useState<PlatformPerformance[]>([]);
  const [kpis, setKpis] = useState<PlatformKPIs | null>(null);
  const [recommendations, setRecommendations] = useState<{
    platform_specific_recommendations: Recommendation[];
    global_recommendations: Recommendation[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch all cross-platform analytics data
        const [overviewRes, performanceRes, kpisRes, recommendationsRes] = await Promise.all([
          fetch('http://localhost:8001/v2/analytics/cross-platform/overview'),
          fetch('http://localhost:8001/v2/analytics/cross-platform/performance'),
          fetch('http://localhost:8001/v2/analytics/cross-platform/kpis'),
          fetch('http://localhost:8001/v2/analytics/cross-platform/recommendations')
        ]);

        if (!overviewRes.ok || !performanceRes.ok || !kpisRes.ok || !recommendationsRes.ok) {
          throw new Error('Failed to fetch cross-platform analytics data');
        }

        const [overviewData, performanceData, kpisData, recommendationsData] = await Promise.all([
          overviewRes.json(),
          performanceRes.json(),
          kpisRes.json(),
          recommendationsRes.json()
        ]);

        setOverview(overviewData.overview);
        setPerformance(performanceData.platforms);
        setKpis(kpisData);
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

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'outline';
    }
  };

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
          <p className="text-muted-foreground">
            Comprehensive performance analysis across all e-commerce platforms
          </p>
        </div>
      </div>

      {/* Platform Summary Cards */}
      {kpis && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatCurrency(kpis.cross_platform_summary.total_revenue)}
              </div>
              <p className="text-xs text-muted-foreground">
                Across {kpis.cross_platform_summary.platforms_analyzed} platforms
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Customers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(kpis.cross_platform_summary.total_customers)}
              </div>
              <p className="text-xs text-muted-foreground">
                Active across all platforms
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Customer Value</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatCurrency(kpis.cross_platform_summary.avg_cross_platform_clv)}
              </div>
              <p className="text-xs text-muted-foreground">
                Cross-platform average
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Order Value</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatCurrency(kpis.cross_platform_summary.avg_cross_platform_aov)}
              </div>
              <p className="text-xs text-muted-foreground">
                Across all orders
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Platform Performance Comparison */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Revenue by Platform</CardTitle>
            <CardDescription>
              Total revenue generated by each platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={performance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="platform" />
                <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
                <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'Revenue']} />
                <Bar dataKey="total_revenue" fill="#0088FE" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Market Share Distribution</CardTitle>
            <CardDescription>
              Revenue share by platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={performance}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ platform, market_share }) => `${platform}: ${market_share.toFixed(1)}%`}
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
          </CardContent>
        </Card>
      </div>

      {/* Platform Performance Scores */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Performance Scores</CardTitle>
          <CardDescription>
            Comprehensive performance analysis including revenue, customers, and efficiency metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={performance} layout="horizontal">
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
        </CardContent>
      </Card>

      {/* Detailed Platform Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Metrics Comparison</CardTitle>
          <CardDescription>
            Detailed comparison of key metrics across platforms
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Platform</th>
                  <th className="text-right p-2">Customers</th>
                  <th className="text-right p-2">Orders</th>
                  <th className="text-right p-2">Revenue</th>
                  <th className="text-right p-2">AOV</th>
                  <th className="text-right p-2">CLV</th>
                  <th className="text-right p-2">Retention</th>
                  <th className="text-right p-2">Growth</th>
                </tr>
              </thead>
              <tbody>
                {performance.map((platform, index) => (
                  <tr key={platform.platform} className="border-b">
                    <td className="p-2 font-medium">{platform.platform}</td>
                    <td className="text-right p-2">{formatNumber(platform.total_customers)}</td>
                    <td className="text-right p-2">{formatNumber(platform.total_orders)}</td>
                    <td className="text-right p-2">{formatCurrency(platform.total_revenue)}</td>
                    <td className="text-right p-2">{formatCurrency(platform.avg_order_value)}</td>
                    <td className="text-right p-2">{formatCurrency(platform.avg_customer_value)}</td>
                    <td className="text-right p-2">{platform.customer_retention_rate.toFixed(1)}%</td>
                    <td className="text-right p-2">
                      <span className={platform.growth_rate > 0 ? 'text-green-600' : 'text-red-600'}>
                        {platform.growth_rate > 0 ? '+' : ''}{platform.growth_rate.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      {recommendations && (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Strategic Recommendations</CardTitle>
              <CardDescription>
                Global recommendations for cross-platform optimization
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {recommendations.global_recommendations.map((rec, index) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant={getPriorityColor(rec.priority)}>
                      {rec.priority} priority
                    </Badge>
                    <Badge variant="outline">{rec.type}</Badge>
                  </div>
                  <p className="text-sm font-medium mb-1">{rec.recommendation}</p>
                  {rec.details && (
                    <p className="text-xs text-muted-foreground">{rec.details}</p>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Platform-Specific Actions</CardTitle>
              <CardDescription>
                Targeted recommendations for individual platforms
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {recommendations.platform_specific_recommendations.slice(0, 6).map((rec, index) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant={getPriorityColor(rec.priority)}>
                      {rec.priority} priority
                    </Badge>
                    <Badge variant="outline">{rec.type}</Badge>
                  </div>
                  <p className="text-sm font-medium mb-1">{rec.recommendation}</p>
                  {rec.potential_impact && (
                    <p className="text-xs text-green-600">{rec.potential_impact}</p>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default CrossPlatformDashboard;