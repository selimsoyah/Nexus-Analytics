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
  Cell,
  ScatterChart,
  Scatter,
  ComposedChart,
  Line,
  Area
} from 'recharts';

// Types for segmentation data
interface SegmentationSummary {
  total_customers: number;
  segment_distribution: Record<string, number>;
  segment_metrics: Record<string, {
    customer_count: number;
    avg_monetary_value: number;
    total_monetary_value: number;
    avg_frequency: number;
    avg_recency_days: number;
    avg_churn_risk: number;
    avg_segment_priority: number;
  }>;
  platform_distribution: Record<string, Record<string, number>>;
  business_metrics: {
    total_revenue: number;
    avg_customer_value: number;
    vip_analysis: {
      vip_customer_count: number;
      vip_revenue: number;
      vip_percentage: number;
      vip_revenue_share: number;
    };
    risk_analysis: {
      high_risk_count: number;
      at_risk_revenue: number;
      risk_percentage: number;
      revenue_at_risk: number;
    };
  };
  segment_performance: Record<string, {
    customer_count: number;
    total_revenue: number;
    avg_customer_value: number;
    avg_churn_risk: number;
  }>;
}

interface RFMData {
  summary: {
    total_customers: number;
    avg_recency_days: number;
    avg_frequency: number;
    avg_monetary_value: number;
    segment_distribution: Record<string, number>;
  };
  rfm_data: Array<{
    customer_id: string;
    platform: string;
    email: string;
    name: string;
    rfm_scores: {
      recency: number;
      frequency: number;
      monetary: number;
      combined: string;
    };
    rfm_values: {
      recency_days: number;
      frequency_count: number;
      monetary_value: number;
      avg_order_value: number;
    };
    segment: string;
    churn_risk_score: number;
    customer_lifespan_days: number;
  }>;
}

interface MLClusterData {
  ml_clustering_results: {
    total_customers: number;
    number_of_clusters: number;
    clusters: Record<string, {
      cluster_name: string;
      customer_count: number;
      characteristics: {
        avg_recency_days: number;
        avg_frequency: number;
        avg_monetary_value: number;
        avg_churn_risk: number;
      };
      top_customers: Array<{
        customer_id: string;
        platform: string;
        monetary_value: number;
      }>;
    }>;
  };
}

// Color schemes for different visualizations
const SEGMENT_COLORS = {
  'Champions': '#2E8B57',
  'Loyal Customers': '#228B22',
  'Potential Loyalists': '#32CD32',
  'New Customers': '#90EE90',
  'Promising': '#98FB98',
  'Need Attention': '#FFD700',
  'About to Sleep': '#FFA500',
  'At Risk': '#FF6347',
  'Cannot Lose Them': '#DC143C',
  'Hibernating': '#8B4513',
  'Lost': '#A0A0A0'
};

const CLUSTER_COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff00ff', '#00ffff', '#800080'];

// Segment Distribution Chart
export const SegmentDistributionChart: React.FC<{ data: SegmentationSummary }> = ({ data }) => {
  const chartData = Object.entries(data.segment_distribution).map(([segment, count]) => ({
    segment,
    count,
    percentage: (count / data.total_customers * 100).toFixed(1)
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <h3 className="text-lg font-semibold mb-4">Customer Segment Distribution</h3>
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ segment, percentage }) => `${segment} (${percentage}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={SEGMENT_COLORS[entry.segment as keyof typeof SEGMENT_COLORS] || CLUSTER_COLORS[index % CLUSTER_COLORS.length]} 
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="segment" 
                angle={-45}
                textAnchor="end"
                height={100}
                fontSize={12}
              />
              <YAxis />
              <Tooltip />
              <Bar 
                dataKey="count" 
                fill="#8884d8"
                name="Customer Count"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

// Segment Performance Chart
export const SegmentPerformanceChart: React.FC<{ data: SegmentationSummary }> = ({ data }) => {
  const chartData = Object.entries(data.segment_performance).map(([segment, metrics]) => ({
    segment,
    customer_count: metrics.customer_count,
    total_revenue: metrics.total_revenue,
    avg_customer_value: metrics.avg_customer_value,
    avg_churn_risk: metrics.avg_churn_risk * 100, // Convert to percentage
    revenue_per_customer: metrics.total_revenue / metrics.customer_count
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <h3 className="text-lg font-semibold mb-4">Segment Performance Analysis</h3>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="segment" 
            angle={-45}
            textAnchor="end"
            height={100}
            fontSize={12}
          />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <Tooltip 
            formatter={(value, name) => {
              const numValue = typeof value === 'number' ? value : parseFloat(value as string);
              if (name === 'avg_churn_risk') return [`${numValue}%`, 'Avg Churn Risk'];
              if (name === 'total_revenue') return [`$${numValue.toFixed(2)}`, 'Total Revenue'];
              if (name === 'avg_customer_value') return [`$${numValue.toFixed(2)}`, 'Avg Customer Value'];
              return [value, name];
            }}
          />
          <Legend />
          <Bar yAxisId="left" dataKey="customer_count" fill="#8884d8" name="Customer Count" />
          <Bar yAxisId="left" dataKey="total_revenue" fill="#82ca9d" name="Total Revenue ($)" />
          <Line yAxisId="right" type="monotone" dataKey="avg_churn_risk" stroke="#ff7300" name="Avg Churn Risk (%)" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

// RFM Heatmap Visualization
export const RFMHeatmapChart: React.FC<{ data: RFMData }> = ({ data }) => {
  // Process RFM data for heatmap
  const heatmapData = data.rfm_data.map(customer => ({
    customer_id: customer.customer_id,
    name: customer.name,
    recency: customer.rfm_scores.recency,
    frequency: customer.rfm_scores.frequency,
    monetary: customer.rfm_scores.monetary,
    segment: customer.segment,
    churn_risk: customer.churn_risk_score * 100
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <h3 className="text-lg font-semibold mb-4">RFM Score Analysis</h3>
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h4 className="text-md font-medium mb-2">RFM Score Distribution</h4>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid />
              <XAxis 
                type="number" 
                dataKey="recency" 
                name="Recency Score" 
                domain={[1, 5]}
                label={{ value: 'Recency Score', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                type="number" 
                dataKey="monetary" 
                name="Monetary Score" 
                domain={[1, 5]}
                label={{ value: 'Monetary Score', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3' }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white p-3 border rounded shadow">
                        <p><strong>{data.name}</strong></p>
                        <p>Segment: {data.segment}</p>
                        <p>R: {data.recency}, F: {data.frequency}, M: {data.monetary}</p>
                        <p>Churn Risk: {data.churn_risk.toFixed(1)}%</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Scatter 
                data={heatmapData} 
                fill="#8884d8"
                r={6}
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div>
          <h4 className="text-md font-medium mb-2">Churn Risk by Segment</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={Object.entries(data.summary.segment_distribution).map(([segment, count]) => {
              const segmentCustomers = data.rfm_data.filter(c => c.segment === segment);
              const avgChurnRisk = segmentCustomers.length > 0 
                ? segmentCustomers.reduce((sum, c) => sum + c.churn_risk_score, 0) / segmentCustomers.length * 100
                : 0;
              
              return {
                segment,
                count,
                avg_churn_risk: avgChurnRisk
              };
            })}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="segment" 
                angle={-45}
                textAnchor="end"
                height={100}
                fontSize={12}
              />
              <YAxis />
              <Tooltip 
                formatter={(value, name) => {
                  const numValue = typeof value === 'number' ? value : parseFloat(value as string);
                  if (name === 'avg_churn_risk') return [`${numValue.toFixed(1)}%`, 'Avg Churn Risk'];
                  return [value, name];
                }}
              />
              <Bar dataKey="avg_churn_risk" fill="#ff7300" name="Avg Churn Risk (%)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

// ML Clustering Visualization
export const MLClusteringChart: React.FC<{ data: MLClusterData }> = ({ data }) => {
  const clusterData = Object.entries(data.ml_clustering_results.clusters).map(([clusterId, cluster]) => ({
    cluster_id: clusterId,
    cluster_name: cluster.cluster_name,
    customer_count: cluster.customer_count,
    avg_recency: cluster.characteristics.avg_recency_days,
    avg_frequency: cluster.characteristics.avg_frequency,
    avg_monetary: cluster.characteristics.avg_monetary_value,
    avg_churn_risk: cluster.characteristics.avg_churn_risk * 100
  }));

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <h3 className="text-lg font-semibold mb-4">ML Clustering Analysis</h3>
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h4 className="text-md font-medium mb-2">Cluster Characteristics</h4>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid />
              <XAxis 
                type="number" 
                dataKey="avg_frequency" 
                name="Avg Frequency" 
                label={{ value: 'Average Frequency', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                type="number" 
                dataKey="avg_monetary" 
                name="Avg Monetary Value" 
                label={{ value: 'Average Monetary Value ($)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                cursor={{ strokeDasharray: '3 3' }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-white p-3 border rounded shadow">
                        <p><strong>{data.cluster_name}</strong></p>
                        <p>Customers: {data.customer_count}</p>
                        <p>Avg Recency: {data.avg_recency.toFixed(1)} days</p>
                        <p>Avg Frequency: {data.avg_frequency.toFixed(1)}</p>
                        <p>Avg Monetary: ${data.avg_monetary.toFixed(2)}</p>
                        <p>Avg Churn Risk: {data.avg_churn_risk.toFixed(1)}%</p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Scatter 
                data={clusterData} 
                fill="#82ca9d"
                r={8}
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
        <div>
          <h4 className="text-md font-medium mb-2">Cluster Distribution</h4>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={clusterData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ cluster_name, customer_count }) => `${cluster_name} (${customer_count})`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="customer_count"
              >
                {clusterData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={CLUSTER_COLORS[index % CLUSTER_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

// Business Impact Metrics
export const BusinessImpactChart: React.FC<{ data: SegmentationSummary }> = ({ data }) => {
  const impactData = [
    {
      metric: 'Total Revenue',
      value: data.business_metrics.total_revenue,
      format: 'currency'
    },
    {
      metric: 'Average Customer Value',
      value: data.business_metrics.avg_customer_value,
      format: 'currency'
    },
    {
      metric: 'VIP Revenue Share',
      value: data.business_metrics.vip_analysis.vip_revenue_share,
      format: 'percentage'
    },
    {
      metric: 'Revenue at Risk',
      value: data.business_metrics.risk_analysis.revenue_at_risk,
      format: 'percentage'
    }
  ];

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <h3 className="text-lg font-semibold mb-4">Business Impact Metrics</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {impactData.map((item, index) => (
          <div key={index} className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {item.format === 'currency' 
                ? `$${item.value.toFixed(2)}` 
                : `${item.value.toFixed(1)}%`
              }
            </div>
            <div className="text-sm text-gray-600 mt-1">{item.metric}</div>
          </div>
        ))}
      </div>
      
      <div className="mt-6">
        <h4 className="text-md font-medium mb-3">VIP vs Risk Analysis</h4>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="p-4 bg-green-50 rounded-lg border-l-4 border-green-400">
            <h5 className="font-semibold text-green-800">VIP Customers</h5>
            <p className="text-sm text-green-700">
              {data.business_metrics.vip_analysis.vip_customer_count} customers 
              ({data.business_metrics.vip_analysis.vip_percentage.toFixed(1)}%)
            </p>
            <p className="text-lg font-bold text-green-800">
              ${data.business_metrics.vip_analysis.vip_revenue.toFixed(2)} revenue
            </p>
          </div>
          <div className="p-4 bg-red-50 rounded-lg border-l-4 border-red-400">
            <h5 className="font-semibold text-red-800">At-Risk Customers</h5>
            <p className="text-sm text-red-700">
              {data.business_metrics.risk_analysis.high_risk_count} customers 
              ({data.business_metrics.risk_analysis.risk_percentage.toFixed(1)}%)
            </p>
            <p className="text-lg font-bold text-red-800">
              ${data.business_metrics.risk_analysis.at_risk_revenue.toFixed(2)} at risk
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Segmentation Analytics Component
export const SegmentationAnalytics: React.FC = () => {
  const [segmentationData, setSegmentationData] = useState<SegmentationSummary | null>(null);
  const [rfmData, setRfmData] = useState<RFMData | null>(null);
  const [clusterData, setClusterData] = useState<MLClusterData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

  useEffect(() => {
    const fetchSegmentationData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all segmentation data in parallel
        const [summaryResponse, rfmResponse, clusterResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/v2/analytics/segmentation/summary`),
          fetch(`${API_BASE_URL}/v2/analytics/segmentation/rfm?include_details=true`),
          fetch(`${API_BASE_URL}/v2/analytics/segmentation/ml-clusters?n_clusters=3`)
        ]);

        if (!summaryResponse.ok || !rfmResponse.ok || !clusterResponse.ok) {
          throw new Error('Failed to fetch segmentation data');
        }

        const [summaryData, rfmDataResponse, clusterDataResponse] = await Promise.all([
          summaryResponse.json(),
          rfmResponse.json(),
          clusterResponse.json()
        ]);

        setSegmentationData(summaryData);
        setRfmData(rfmDataResponse);
        setClusterData(clusterDataResponse);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchSegmentationData();
  }, [API_BASE_URL]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading segmentation data</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!segmentationData || !rfmData || !clusterData) {
    return (
      <div className="text-center text-gray-500 p-8">
        <p>No segmentation data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Customer Segmentation Analytics</h2>
        <p className="text-gray-600">Advanced customer analysis using RFM and ML clustering</p>
      </div>

      <BusinessImpactChart data={segmentationData} />
      <SegmentDistributionChart data={segmentationData} />
      <SegmentPerformanceChart data={segmentationData} />
      <RFMHeatmapChart data={rfmData} />
      <MLClusteringChart data={clusterData} />
    </div>
  );
};