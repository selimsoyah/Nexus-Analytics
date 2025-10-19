'use client';

import React, { useState } from 'react';
import ProtectedRoute from '@/app/protectedRoute';
import { Brain, TrendingUp, Target, Users } from 'lucide-react';
import MLCLVDashboard from '@/components/MLCLVDashboard';
import { CLVAnalytics } from '@/components/charts/CLVCharts';
import { useAnalyticsFilters } from '@/hooks/useAnalytics';

export default function CLVPage() {
  const { filters, updateFilter } = useAnalyticsFilters();
  const [activeTab, setActiveTab] = useState<'ml' | 'overview' | 'traditional'>('ml');

  const handleFiltersChange = (newFilters: any) => {
    Object.entries(newFilters).forEach(([key, value]) => {
      updateFilter(key as any, value);
    });
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-blue-600 mr-3" />
                <h1 className="text-2xl font-bold text-gray-900">CLV Analytics</h1>
                <span className="ml-3 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                  🤖 ML Enhanced
                </span>
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
                  <option value="amazon">Amazon</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {[
                { key: 'ml', label: '🧠 ML Predictions', icon: Brain },
                { key: 'overview', label: '📊 Analytics Overview', icon: TrendingUp },
                { key: 'traditional', label: '📈 Traditional CLV', icon: Target }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key as any)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4 inline mr-2" />
                  {label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div>
            {activeTab === 'ml' && (
              <MLCLVDashboard filters={filters} />
            )}

            {activeTab === 'overview' && (
              <CLVAnalytics filters={filters} />
            )}

            {activeTab === 'traditional' && (
              <div className="space-y-6">
                {/* Traditional CLV Explanation */}
                <div className="bg-white rounded-lg shadow border p-6">
                  <h3 className="text-lg font-semibold mb-4">Traditional CLV Analysis</h3>
                  <div className="bg-gray-50 p-4 rounded-lg mb-4">
                    <h4 className="font-medium mb-2">Basic CLV Formula:</h4>
                    <code className="text-sm">CLV = Average Order Value × Purchase Frequency × Customer Lifespan</code>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="border rounded p-4">
                      <h5 className="font-medium text-gray-700">Advantages</h5>
                      <ul className="text-sm text-gray-600 mt-2 space-y-1">
                        <li>• Simple to calculate</li>
                        <li>• Easy to understand</li>
                        <li>• Quick implementation</li>
                      </ul>
                    </div>
                    
                    <div className="border rounded p-4">
                      <h5 className="font-medium text-gray-700">Limitations</h5>
                      <ul className="text-sm text-gray-600 mt-2 space-y-1">
                        <li>• Based on historical data only</li>
                        <li>• No predictive capability</li>
                        <li>• Ignores behavioral patterns</li>
                      </ul>
                    </div>
                    
                    <div className="border rounded p-4">
                      <h5 className="font-medium text-gray-700">Use Cases</h5>
                      <ul className="text-sm text-gray-600 mt-2 space-y-1">
                        <li>• Basic segmentation</li>
                        <li>• Historical analysis</li>
                        <li>• Simple reporting</li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Traditional CLV Charts */}
                <CLVAnalytics filters={filters} />
              </div>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}