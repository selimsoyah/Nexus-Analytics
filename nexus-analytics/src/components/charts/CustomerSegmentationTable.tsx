import React, { useState, useEffect } from 'react';

// Types for customer profile data
interface CustomerProfile {
  customer_id: string;
  platform: string;
  rfm_analysis: {
    recency_score: number;
    frequency_score: number;
    monetary_score: number;
    rfm_score: string;
    recency_days: number;
    frequency_count: number;
    monetary_value: number;
  };
  segmentation: {
    rfm_segment: string;
    ml_segment: string;
    business_segment: string;
    segment_priority: number;
    segment_confidence: number;
  };
  metrics: {
    avg_order_value: number;
    customer_lifespan_days: number;
    churn_risk_score: number;
  };
  recommendations: {
    actions: string[];
    priority_level: number;
  };
}

interface CustomerProfilesResponse {
  profiles: CustomerProfile[];
  summary: {
    total_profiles: number;
    platform_filter: string | null;
    segment_filter: string | null;
    sort_criteria: string;
  };
}

// Customer Profile Table Component
export const CustomerProfileTable: React.FC = () => {
  const [profiles, setProfiles] = useState<CustomerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<string>('monetary');
  const [segmentFilter, setSegmentFilter] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalProfiles, setTotalProfiles] = useState(0);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
  const itemsPerPage = 10;

  const fetchProfiles = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        limit: itemsPerPage.toString(),
        sort_by: sortBy
      });

      if (segmentFilter) {
        params.append('segment', segmentFilter);
      }

      const response = await fetch(`${API_BASE_URL}/v2/analytics/segmentation/profiles?${params}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch customer profiles');
      }

      const data: CustomerProfilesResponse = await response.json();
      setProfiles(data.profiles);
      setTotalProfiles(data.summary.total_profiles);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, [sortBy, segmentFilter]);

  const getRiskBadgeColor = (riskScore: number) => {
    if (riskScore > 0.7) return 'bg-red-100 text-red-800';
    if (riskScore > 0.4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  const getRiskLabel = (riskScore: number) => {
    if (riskScore > 0.7) return 'High Risk';
    if (riskScore > 0.4) return 'Medium Risk';
    return 'Low Risk';
  };

  const getSegmentBadgeColor = (segment: string) => {
    const colorMap: Record<string, string> = {
      'Champions': 'bg-green-100 text-green-800',
      'Loyal Customers': 'bg-blue-100 text-blue-800',
      'Potential Loyalists': 'bg-purple-100 text-purple-800',
      'New Customers': 'bg-cyan-100 text-cyan-800',
      'Promising': 'bg-indigo-100 text-indigo-800',
      'Need Attention': 'bg-yellow-100 text-yellow-800',
      'About to Sleep': 'bg-orange-100 text-orange-800',
      'At Risk': 'bg-red-100 text-red-800',
      'Cannot Lose Them': 'bg-pink-100 text-pink-800',
      'Hibernating': 'bg-gray-100 text-gray-800',
      'Lost': 'bg-slate-100 text-slate-800'
    };
    return colorMap[segment] || 'bg-gray-100 text-gray-800';
  };

  const uniqueSegments = Array.from(new Set(profiles.map(p => p.segmentation.business_segment)));

  if (loading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <div className="text-red-600">
          <h3 className="font-semibold">Error loading customer profiles</h3>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Customer Profiles</h3>
        <div className="flex gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="monetary">Monetary Value</option>
              <option value="frequency">Purchase Frequency</option>
              <option value="recency">Recency</option>
              <option value="risk">Churn Risk</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Segment</label>
            <select
              value={segmentFilter}
              onChange={(e) => setSegmentFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="">All Segments</option>
              {uniqueSegments.map(segment => (
                <option key={segment} value={segment}>{segment}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {profiles.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <p>No customer profiles found</p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Segment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    RFM Scores
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Value & Risk
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {profiles.map((profile) => (
                  <tr key={profile.customer_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          Customer {profile.customer_id}
                        </div>
                        <div className="text-sm text-gray-500">
                          {profile.platform}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="space-y-1">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSegmentBadgeColor(profile.segmentation.business_segment)}`}>
                          {profile.segmentation.business_segment}
                        </span>
                        <div className="text-xs text-gray-500">
                          ML: {profile.segmentation.ml_segment}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="text-center">
                          <div className="font-medium">R: {profile.rfm_analysis.recency_score}</div>
                          <div className="text-gray-500">{profile.rfm_analysis.recency_days}d</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium">F: {profile.rfm_analysis.frequency_score}</div>
                          <div className="text-gray-500">{profile.rfm_analysis.frequency_count}</div>
                        </div>
                        <div className="text-center">
                          <div className="font-medium">M: {profile.rfm_analysis.monetary_score}</div>
                          <div className="text-gray-500">${profile.rfm_analysis.monetary_value.toFixed(0)}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="space-y-1">
                        <div className="text-sm font-medium text-gray-900">
                          ${profile.rfm_analysis.monetary_value.toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-500">
                          AOV: ${profile.metrics.avg_order_value.toFixed(2)}
                        </div>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskBadgeColor(profile.metrics.churn_risk_score)}`}>
                          {getRiskLabel(profile.metrics.churn_risk_score)}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        <div className="text-xs text-gray-500">
                          Priority: {profile.segmentation.segment_priority}
                        </div>
                        <div className="max-w-48">
                          {profile.recommendations.actions.slice(0, 2).map((action, index) => (
                            <div key={index} className="text-xs text-blue-600 mb-1">
                              • {action}
                            </div>
                          ))}
                          {profile.recommendations.actions.length > 2 && (
                            <div className="text-xs text-gray-400">
                              +{profile.recommendations.actions.length - 2} more
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-6 flex justify-between items-center">
            <div className="text-sm text-gray-700">
              Showing {profiles.length} of {totalProfiles} profiles
            </div>
            <div className="text-sm text-gray-500">
              Sorted by {sortBy} • {segmentFilter || 'All segments'}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Segment Overview Cards Component
export const SegmentOverviewCards: React.FC<{ summary: any }> = ({ summary }) => {
  const segmentCards = Object.entries(summary.segment_metrics || {}).map(([segment, metrics]: [string, any]) => ({
    segment,
    ...metrics
  }));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {segmentCards.map((card) => (
        <div key={card.segment} className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">{card.segment}</h3>
            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSegmentBadgeColor(card.segment)}`}>
              {card.customer_count} customers
            </span>
          </div>
          
          <div className="mt-4 space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Total Revenue:</span>
              <span className="text-sm font-medium">${card.total_monetary_value?.toFixed(2) || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg Customer Value:</span>
              <span className="text-sm font-medium">${card.avg_monetary_value?.toFixed(2) || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg Frequency:</span>
              <span className="text-sm font-medium">{card.avg_frequency?.toFixed(1) || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Avg Recency:</span>
              <span className="text-sm font-medium">{card.avg_recency_days?.toFixed(0) || 0} days</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Churn Risk:</span>
              <span className={`text-sm font-medium ${card.avg_churn_risk > 0.7 ? 'text-red-600' : card.avg_churn_risk > 0.4 ? 'text-yellow-600' : 'text-green-600'}`}>
                {(card.avg_churn_risk * 100)?.toFixed(1) || 0}%
              </span>
            </div>
          </div>
          
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="text-xs text-gray-500">
              Priority Level: {card.avg_segment_priority?.toFixed(0) || 'N/A'}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Helper function for segment badge colors (duplicated for use in this file)
const getSegmentBadgeColor = (segment: string) => {
  const colorMap: Record<string, string> = {
    'Champions': 'bg-green-100 text-green-800',
    'Loyal Customers': 'bg-blue-100 text-blue-800',
    'Potential Loyalists': 'bg-purple-100 text-purple-800',
    'New Customers': 'bg-cyan-100 text-cyan-800',
    'Promising': 'bg-indigo-100 text-indigo-800',
    'Need Attention': 'bg-yellow-100 text-yellow-800',
    'About to Sleep': 'bg-orange-100 text-orange-800',
    'At Risk': 'bg-red-100 text-red-800',
    'Cannot Lose Them': 'bg-pink-100 text-pink-800',
    'Hibernating': 'bg-gray-100 text-gray-800',
    'Lost': 'bg-slate-100 text-slate-800'
  };
  return colorMap[segment] || 'bg-gray-100 text-gray-800';
};