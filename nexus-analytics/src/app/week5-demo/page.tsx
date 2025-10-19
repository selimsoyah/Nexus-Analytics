'use client';

import React, { useState } from 'react';

const Week5Demo: React.FC = () => {
  const [apiResponse, setApiResponse] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const testAPI = async (endpoint: string, description: string) => {
    setLoading(true);
    try {
      // Test without authentication first to see the structure
      const response = await fetch(`http://localhost:8001${endpoint}`);
      const data = await response.json();
      
      setApiResponse(`
🔥 ${description}
📡 Endpoint: ${endpoint}
📋 Response:
${JSON.stringify(data, null, 2)}
      `);
    } catch (error) {
      setApiResponse(`❌ Error testing ${endpoint}: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Week 5 Platform Integration Demo</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-8">
        <button
          onClick={() => testAPI('/health', 'Basic Health Check')}
          className="p-4 bg-blue-500 text-white rounded hover:bg-blue-600"
          disabled={loading}
        >
          🏥 Test Health Endpoint
        </button>
        
        <button
          onClick={() => testAPI('/v2/analytics/cross-platform/overview', 'Cross-Platform Overview')}
          className="p-4 bg-green-500 text-white rounded hover:bg-green-600"
          disabled={loading}
        >
          🌐 Cross-Platform Overview
        </button>
        
        <button
          onClick={() => testAPI('/v2/analytics/cross-platform/performance', 'Platform Performance')}
          className="p-4 bg-purple-500 text-white rounded hover:bg-purple-600"
          disabled={loading}
        >
          📊 Platform Performance
        </button>
        
        <button
          onClick={() => testAPI('/v2/analytics/cross-platform/kpis', 'Platform KPIs')}
          className="p-4 bg-orange-500 text-white rounded hover:bg-orange-600"
          disabled={loading}
        >
          📈 Platform KPIs
        </button>
        
        <button
          onClick={() => testAPI('/v2/analytics/cross-platform/recommendations', 'AI Recommendations')}
          className="p-4 bg-red-500 text-white rounded hover:bg-red-600"
          disabled={loading}
        >
          🤖 AI Recommendations
        </button>
        
        <button
          onClick={() => testAPI('/v2/analytics/cross-platform/predictions', 'ML Predictions')}
          className="p-4 bg-indigo-500 text-white rounded hover:bg-indigo-600"
          disabled={loading}
        >
          🔮 ML Predictions
        </button>
      </div>

      <div className="bg-gray-900 text-green-400 p-6 rounded-lg font-mono text-sm overflow-auto max-h-96">
        <h3 className="text-white text-lg mb-4">API Response:</h3>
        {loading ? (
          <div>⏳ Loading...</div>
        ) : (
          <pre>{apiResponse || 'Click a button above to test the Week 5 APIs'}</pre>
        )}
      </div>

      <div className="mt-8 bg-blue-50 p-6 rounded-lg">
        <h2 className="text-xl font-bold mb-4">🎯 Week 5 Accomplishments</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="font-semibold mb-2">✅ Backend Integration Platform</h3>
            <ul className="text-sm space-y-1">
              <li>• WooCommerce Connector (784 lines)</li>
              <li>• Multi-Platform Manager (600+ lines)</li>
              <li>• Universal Schema Mapping (600+ lines)</li>
              <li>• Data Synchronization Pipeline</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-2">🧠 ML & Analytics Engine</h3>
            <ul className="text-sm space-y-1">
              <li>• Customer Segmentation (RFM)</li>
              <li>• Sales Forecasting Models</li>
              <li>• Product Performance Analysis</li>
              <li>• Data Quality Framework</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-2">🏭 Production Features</h3>
            <ul className="text-sm space-y-1">
              <li>• System Health Monitoring</li>
              <li>• Performance Metrics</li>
              <li>• Deployment Validation</li>
              <li>• Comprehensive Testing Suite</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold mb-2">📊 Frontend Interfaces</h3>
            <ul className="text-sm space-y-1">
              <li>• Cross-Platform Dashboard</li>
              <li>• Enhanced CLV Analytics</li>
              <li>• Real-time Data Visualization</li>
              <li>• Admin-level Access Controls</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Week5Demo;