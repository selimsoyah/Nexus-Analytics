'use client';

// Dashboard Layout Components
// Layout and UI components for the analytics dashboard

import React, { useState, useCallback } from 'react';
import { RefreshCw, Filter, Calendar, BarChart3, TrendingUp, Users, Package } from 'lucide-react';
import { AnalyticsFilters } from '@/types/analytics';
import { formatCurrency, formatNumber, cn } from '@/components/charts/ChartUtils';

interface DashboardLayoutProps {
  children: React.ReactNode;
  filters: AnalyticsFilters;
  onFiltersChange: (filters: AnalyticsFilters) => void;
  onRefresh?: () => void;
  lastUpdated?: Date;
  loading?: boolean;
}

export function DashboardLayout({ 
  children, 
  filters, 
  onFiltersChange, 
  onRefresh,
  lastUpdated,
  loading = false
}: DashboardLayoutProps) {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'customers', name: 'Customers', icon: Users },
    { id: 'products', name: 'Products', icon: Package },
    { id: 'sales', name: 'Sales', icon: TrendingUp },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <PlatformSelector
                value={filters.platform || 'all'}
                onChange={(platform) => onFiltersChange({ ...filters, platform: platform === 'all' ? undefined : platform })}
              />
              
              <button
                onClick={onRefresh}
                disabled={loading}
                className={cn(
                  "inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500",
                  loading && "opacity-50 cursor-not-allowed"
                )}
              >
                <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "group inline-flex items-center py-2 px-1 border-b-2 font-medium text-sm",
                    activeTab === tab.id
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  )}
                >
                  <Icon className="h-5 w-5 mr-2" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {lastUpdated && (
          <div className="mb-6 text-sm text-gray-500">
            Last updated: {lastUpdated.toLocaleString()}
          </div>
        )}

        <div className="space-y-6">
          {children}
        </div>
      </div>
    </div>
  );
}

interface PlatformSelectorProps {
  value: string;
  onChange: (platform: string) => void;
}

function PlatformSelector({ value, onChange }: PlatformSelectorProps) {
  const platforms = [
    { value: 'all', label: 'All Platforms' },
    { value: 'generic_csv', label: 'Generic CSV' },
    { value: 'shopify', label: 'Shopify' },
    { value: 'woocommerce', label: 'WooCommerce' },
    { value: 'magento', label: 'Magento' },
  ];

  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="block w-40 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
      >
        {platforms.map((platform) => (
          <option key={platform.value} value={platform.value}>
            {platform.label}
          </option>
        ))}
      </select>
    </div>
  );
}

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon?: React.ComponentType<{ className?: string }>;
  loading?: boolean;
}

export function MetricCard({ 
  title, 
  value, 
  change, 
  changeType = 'neutral', 
  icon: Icon,
  loading = false 
}: MetricCardProps) {
  if (loading) {
    return (
      <div className="bg-white overflow-hidden shadow rounded-lg">
        <div className="p-5">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-gray-200 rounded animate-pulse"></div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <div className="h-4 bg-gray-200 rounded animate-pulse mb-2"></div>
              <div className="h-6 bg-gray-200 rounded animate-pulse"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            {Icon && <Icon className="h-8 w-8 text-gray-400" />}
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">
                  {typeof value === 'number' ? formatNumber(value) : value}
                </div>
                {change !== undefined && (
                  <div className={cn(
                    "ml-2 flex items-baseline text-sm font-semibold",
                    changeType === 'increase' && "text-green-600",
                    changeType === 'decrease' && "text-red-600",
                    changeType === 'neutral' && "text-gray-500"
                  )}>
                    {change > 0 ? '+' : ''}{change.toFixed(1)}%
                    {changeType === 'increase' && (
                      <TrendingUp className="h-4 w-4 ml-1" />
                    )}
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}

interface TabContentProps {
  activeTab: string;
  children: React.ReactNode;
}

export function TabContent({ activeTab, children }: TabContentProps) {
  return (
    <div className="space-y-6">
      {children}
    </div>
  );
}

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
      <span className="ml-2 text-gray-600">Loading analytics...</span>
    </div>
  );
}

export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-md p-4">
      <div className="flex">
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-800">Error loading analytics</h3>
          <div className="mt-2 text-sm text-red-700">
            {message}
          </div>
        </div>
      </div>
    </div>
  );
}