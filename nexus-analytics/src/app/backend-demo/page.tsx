'use client';

import React, { useState } from 'react';

const BackendAPIDemo: React.FC = () => {
  const [testResults, setTestResults] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  const testEndpoint = async (endpoint: string, description: string, key: string) => {
    setLoading(prev => ({ ...prev, [key]: true }));
    
    try {
      const response = await fetch(`http://localhost:8001${endpoint}`);
      const data = await response.json();
      
      setTestResults(prev => ({
        ...prev,
        [key]: {
          success: response.ok,
          status: response.status,
          data: data,
          description: description
        }
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [key]: {
          success: false,
          error: error.message,
          description: description
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const endpoints = [
    {
      key: 'health',
      endpoint: '/health',
      description: 'Basic System Health',
      color: 'bg-blue-500 hover:bg-blue-600'
    },
    {
      key: 'cross_platform_overview',
      endpoint: '/v2/analytics/cross-platform/overview',
      description: 'Cross-Platform Overview (WooCommerce + Shopify)',
      color: 'bg-green-500 hover:bg-green-600'
    },
    {
      key: 'platform_performance',
      endpoint: '/v2/analytics/cross-platform/performance',
      description: 'WooCommerce vs Shopify Performance',
      color: 'bg-purple-500 hover:bg-purple-600'
    },
    {
      key: 'platform_kpis',
      endpoint: '/v2/analytics/cross-platform/kpis',
      description: 'Multi-Platform KPIs',
      color: 'bg-orange-500 hover:bg-orange-600'
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-4">🔧 Week 5 Backend API Demo</h1>
        <p className="text-gray-600 mb-4">
          Test the actual WooCommerce integration APIs we built in Week 5. These endpoints demonstrate 
          that your backend now supports multiple e-commerce platforms with unified analytics.
        </p>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-yellow-800 mb-2">💡 What You're Testing:</h3>
          <p className="text-sm text-yellow-700">
            The buttons below call the actual backend APIs that handle WooCommerce integration. 
            Even without live WooCommerce credentials, you can see the API structure and responses 
            that demonstrate the multi-platform capability.
          </p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2 mb-8">
        {endpoints.map(({ key, endpoint, description, color }) => (
          <button
            key={key}
            onClick={() => testEndpoint(endpoint, description, key)}
            disabled={loading[key]}
            className={`p-4 text-white rounded-lg transition-colors ${color} ${
              loading[key] ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {loading[key] ? (
              <span>⏳ Testing...</span>
            ) : (
              <span>{description}</span>
            )}
          </button>
        ))}
      </div>

      {/* Results Display */}
      <div className="space-y-6">
        {Object.entries(testResults).map(([key, result]) => (
          <div key={key} className="bg-white border rounded-lg shadow-sm">
            <div className="p-4 border-b bg-gray-50">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">{result.description}</h3>
                <span className={`px-2 py-1 rounded text-sm ${
                  result.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {result.success ? '✅ Success' : '❌ Error'}
                </span>
              </div>
              {result.status && (
                <p className="text-sm text-gray-600 mt-1">Status: {result.status}</p>
              )}
            </div>
            
            <div className="p-4">
              <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-auto max-h-64">
                {result.data ? JSON.stringify(result.data, null, 2) : result.error}
              </pre>
            </div>
          </div>
        ))}
      </div>

      {/* Architecture Explanation */}
      <div className="mt-12 bg-blue-50 rounded-lg p-6">
        <h2 className="text-xl font-bold text-blue-900 mb-4">🏗️ Week 5 Architecture Overview</h2>
        
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold mb-3">📁 Backend Files Created:</h3>
            <ul className="text-sm space-y-1">
              <li>• <code>woocommerce_connector.py</code> (784 lines)</li>
              <li>• <code>woocommerce_schema_mapper.py</code> (600+ lines)</li>
              <li>• <code>woocommerce_data_sync.py</code> (600+ lines)</li>
              <li>• <code>platform_manager.py</code> (641 lines)</li>
              <li>• <code>ml_analytics.py</code> (700+ lines)</li>
              <li>• <code>data_quality.py</code> (650+ lines)</li>
              <li>• <code>production_monitor.py</code> (700+ lines)</li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold mb-3">🔄 Data Flow:</h3>
            <div className="text-sm space-y-2">
              <div className="bg-white p-2 rounded border">
                1. WooCommerce Store → WooCommerce API
              </div>
              <div className="bg-white p-2 rounded border">
                2. WooCommerce Connector → Data Extraction
              </div>
              <div className="bg-white p-2 rounded border">
                3. Schema Mapper → Universal Format
              </div>
              <div className="bg-white p-2 rounded border">
                4. Analytics Engine → Cross-Platform Insights
              </div>
              <div className="bg-white p-2 rounded border">
                5. Frontend Dashboard → Visualization
              </div>
            </div>
          </div>
        </div>
        
        <div className="mt-6 p-4 bg-white rounded border">
          <h4 className="font-semibold mb-2">🎯 The Key Difference:</h4>
          <p className="text-sm text-gray-700">
            <strong>Before Week 5:</strong> Nexus Analytics only worked with Shopify stores.<br/>
            <strong>After Week 5:</strong> Nexus Analytics can connect to WooCommerce, Shopify, and has an extensible 
            architecture for adding Magento, BigCommerce, and other platforms. All platforms use the same universal 
            data schema for unified analytics and cross-platform comparisons.
          </p>
        </div>
      </div>
    </div>
  );
};

export default BackendAPIDemo;