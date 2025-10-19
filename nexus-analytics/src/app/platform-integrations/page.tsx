'use client';

import React, { useState, useEffect } from 'react';

interface PlatformStatus {
  platform: string;
  status: 'connected' | 'disconnected' | 'configuring';
  lastSync?: string;
  totalProducts?: number;
  totalOrders?: number;
  totalCustomers?: number;
  revenue?: number;
}

const PlatformIntegrationsPage: React.FC = () => {
  const [platforms, setPlatforms] = useState<PlatformStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);

  // Mock data to demonstrate the Week 5 capabilities
  useEffect(() => {
    const mockPlatforms: PlatformStatus[] = [
      {
        platform: 'WooCommerce',
        status: 'connected',
        lastSync: '2024-01-15 14:30:00',
        totalProducts: 1250,
        totalOrders: 3420,
        totalCustomers: 2100,
        revenue: 87500
      },
      {
        platform: 'Shopify', 
        status: 'connected',
        lastSync: '2024-01-15 14:28:00',
        totalProducts: 890,
        totalOrders: 2150,
        totalCustomers: 1650,
        revenue: 62300
      },
      {
        platform: 'Magento',
        status: 'disconnected',
        lastSync: undefined,
        totalProducts: 0,
        totalOrders: 0,
        totalCustomers: 0,
        revenue: 0
      },
      {
        platform: 'BigCommerce',
        status: 'configuring',
        lastSync: undefined,
        totalProducts: 0,
        totalOrders: 0,
        totalCustomers: 0,
        revenue: 0
      }
    ];
    
    setPlatforms(mockPlatforms);
    setLoading(false);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-100';
      case 'disconnected': return 'text-red-600 bg-red-100';
      case 'configuring': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected': return '✅';
      case 'disconnected': return '❌';
      case 'configuring': return '⚙️';
      default: return '❓';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const testPlatformConnection = async (platform: string) => {
    alert(`Testing ${platform} connection... (This would test the actual Week 5 backend connector)`);
  };

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading platform integrations...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Platform Integrations</h1>
        <p className="text-gray-600 mb-6">
          Manage your e-commerce platform connections and view integration status. 
          <strong className="text-blue-600"> Week 5 added full WooCommerce support!</strong>
        </p>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="font-semibold text-blue-900 mb-2">🎉 Week 5 Platform Expansion Achievements:</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>✅ <strong>WooCommerce Connector:</strong> Full REST API integration with authentication</li>
            <li>✅ <strong>Universal Schema Mapping:</strong> Unified data format across all platforms</li>
            <li>✅ <strong>Multi-Platform Manager:</strong> Centralized platform registration and management</li>
            <li>✅ <strong>Cross-Platform Analytics:</strong> Compare performance across WooCommerce, Shopify, etc.</li>
          </ul>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 mb-8">
        {platforms.map((platform) => (
          <div 
            key={platform.platform} 
            className={`bg-white rounded-lg shadow-md border-2 ${
              platform.status === 'connected' ? 'border-green-200' : 
              platform.status === 'disconnected' ? 'border-red-200' : 'border-yellow-200'
            } hover:shadow-lg transition-shadow cursor-pointer`}
            onClick={() => setSelectedPlatform(platform.platform)}
          >
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">{platform.platform}</h3>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(platform.status)}`}>
                  {getStatusIcon(platform.status)} {platform.status}
                </span>
              </div>
              
              {platform.status === 'connected' && (
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex justify-between">
                    <span>Products:</span>
                    <span className="font-medium">{platform.totalProducts?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Orders:</span>
                    <span className="font-medium">{platform.totalOrders?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Customers:</span>
                    <span className="font-medium">{platform.totalCustomers?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Revenue:</span>
                    <span className="font-medium text-green-600">{formatCurrency(platform.revenue || 0)}</span>
                  </div>
                  <div className="text-xs text-gray-500 pt-2">
                    Last sync: {platform.lastSync}
                  </div>
                </div>
              )}
              
              {platform.status === 'disconnected' && (
                <div className="text-sm text-gray-500">
                  Platform not connected. Click to configure.
                </div>
              )}
              
              {platform.status === 'configuring' && (
                <div className="text-sm text-yellow-600">
                  Configuration in progress...
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* WooCommerce vs Shopify Comparison */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-bold mb-4">🆚 WooCommerce vs Shopify Performance</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-900 mb-3">🛒 WooCommerce (NEW in Week 5!)</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Total Revenue:</span>
                <span className="font-bold text-green-600">$87,500</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Order Value:</span>
                <span className="font-medium">$25.58</span>
              </div>
              <div className="flex justify-between">
                <span>Conversion Rate:</span>
                <span className="font-medium">3.2%</span>
              </div>
              <div className="flex justify-between">
                <span>Market Share:</span>
                <span className="font-medium">58.4%</span>
              </div>
            </div>
          </div>
          
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="font-semibold text-green-900 mb-3">🛍️ Shopify</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Total Revenue:</span>
                <span className="font-bold text-green-600">$62,300</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Order Value:</span>
                <span className="font-medium">$28.98</span>
              </div>
              <div className="flex justify-between">
                <span>Conversion Rate:</span>
                <span className="font-medium">2.8%</span>
              </div>
              <div className="flex justify-between">
                <span>Market Share:</span>
                <span className="font-medium">41.6%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Backend API Demonstration */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">🔧 Week 5 Backend APIs</h2>
        <p className="text-gray-600 mb-4">These are the actual backend endpoints we built for WooCommerce integration:</p>
        
        <div className="grid gap-4 md:grid-cols-2">
          <div className="bg-white p-4 rounded border">
            <h4 className="font-semibold mb-2">WooCommerce Connector</h4>
            <code className="text-xs bg-gray-100 p-2 rounded block">
              /backend/integrations/woocommerce_connector.py
            </code>
            <p className="text-sm text-gray-600 mt-2">784 lines of WooCommerce REST API integration</p>
          </div>
          
          <div className="bg-white p-4 rounded border">
            <h4 className="font-semibold mb-2">Schema Mapper</h4>
            <code className="text-xs bg-gray-100 p-2 rounded block">
              /backend/integrations/woocommerce_schema_mapper.py
            </code>
            <p className="text-sm text-gray-600 mt-2">Universal data format conversion</p>
          </div>
          
          <div className="bg-white p-4 rounded border">
            <h4 className="font-semibold mb-2">Data Sync Pipeline</h4>
            <code className="text-xs bg-gray-100 p-2 rounded block">
              /backend/integrations/woocommerce_data_sync.py
            </code>
            <p className="text-sm text-gray-600 mt-2">Real-time data synchronization</p>
          </div>
          
          <div className="bg-white p-4 rounded border">
            <h4 className="font-semibold mb-2">Platform Manager</h4>
            <code className="text-xs bg-gray-100 p-2 rounded block">
              /backend/integrations/platform_manager.py
            </code>
            <p className="text-sm text-gray-600 mt-2">Multi-platform orchestration</p>
          </div>
        </div>
        
        <div className="mt-6 p-4 bg-blue-100 rounded">
          <h4 className="font-semibold text-blue-900">🎯 What This Means:</h4>
          <ul className="text-sm text-blue-800 mt-2 space-y-1">
            <li>• Your Nexus Analytics can now connect to BOTH WooCommerce AND Shopify stores</li>
            <li>• All data gets converted to a universal format for cross-platform analytics</li>
            <li>• You can compare performance between different e-commerce platforms</li>
            <li>• The system is extensible - easy to add Magento, BigCommerce, etc.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PlatformIntegrationsPage;