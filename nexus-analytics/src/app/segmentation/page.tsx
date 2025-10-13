'use client';

// Customer Segmentation Page
// Dedicated page for advanced customer segmentation analysis

import React, { useState, useEffect } from 'react';
import { Users, Target, TrendingUp, AlertTriangle } from 'lucide-react';
import ProtectedRoute from '@/app/protectedRoute';
import { SegmentationAnalytics } from '@/components/charts/SegmentationCharts';
import { CustomerProfileTable, SegmentOverviewCards } from '@/components/charts/CustomerSegmentationTable';

export default function SegmentationPage() {
  const [segmentationSummary, setSegmentationSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<string>('');

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

  useEffect(() => {
    const fetchSegmentationSummary = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`${API_BASE_URL}/v2/analytics/segmentation/summary`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch segmentation summary');
        }

        const data = await response.json();
        setSegmentationSummary(data);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchSegmentationSummary();
  }, [API_BASE_URL]);

  const handleRefresh = () => {
    window.location.reload();
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  if (error) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 p-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error loading segmentation data</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={handleRefresh}
                    className="bg-red-100 hover:bg-red-200 text-red-800 px-4 py-2 rounded text-sm"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
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
                <Users className="h-8 w-8 text-blue-600 mr-3" />
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Customer Segmentation</h1>
                  <p className="text-sm text-gray-600">Advanced customer analysis and targeting</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleRefresh}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Refresh Analysis
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Key Metrics */}
          {segmentationSummary && (
            <div className="mb-8">
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-6">
                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <Users className="h-8 w-8 text-blue-400" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Total Customers</dt>
                          <dd className="text-2xl font-semibold text-gray-900">
                            {segmentationSummary.total_customers}
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
                        <Target className="h-8 w-8 text-green-400" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Active Segments</dt>
                          <dd className="text-2xl font-semibold text-gray-900">
                            {Object.keys(segmentationSummary.segment_distribution).length}
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
                        <TrendingUp className="h-8 w-8 text-purple-400" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">Total Revenue</dt>
                          <dd className="text-2xl font-semibold text-gray-900">
                            ${segmentationSummary.business_metrics?.total_revenue?.toFixed(2) || '0.00'}
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
                        <AlertTriangle className="h-8 w-8 text-orange-400" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">At-Risk Revenue</dt>
                          <dd className="text-2xl font-semibold text-gray-900">
                            {segmentationSummary.business_metrics?.risk_analysis?.revenue_at_risk?.toFixed(1) || '0.0'}%
                          </dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Segment Overview Cards */}
              <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Segment Overview</h2>
                <SegmentOverviewCards summary={segmentationSummary} />
              </div>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="mb-8">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                {[
                  { id: 'charts', name: 'Visual Analysis', icon: TrendingUp },
                  { id: 'customers', name: 'Customer Profiles', icon: Users },
                ].map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setSelectedSegment(tab.id)}
                      className={`${
                        selectedSegment === tab.id || (selectedSegment === '' && tab.id === 'charts')
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

          {/* Tab Content */}
          <div className="space-y-6">
            {(selectedSegment === 'charts' || selectedSegment === '') && (
              <SegmentationAnalytics />
            )}

            {selectedSegment === 'customers' && (
              <div className="space-y-6">
                <CustomerProfileTable />
              </div>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}