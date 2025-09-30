// Chart Utilities
// Common functions and utilities for chart components

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, parseISO } from "date-fns";

// Utility function for combining class names
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Color palette for charts
export const CHART_COLORS = {
  primary: '#3B82F6',      // Blue
  secondary: '#10B981',     // Green
  accent: '#F59E0B',       // Yellow
  danger: '#EF4444',       // Red
  purple: '#8B5CF6',       // Purple
  pink: '#EC4899',         // Pink
  indigo: '#6366F1',       // Indigo
  teal: '#14B8A6',         // Teal
};

export const PLATFORM_COLORS = {
  shopify: '#95BF47',      // Shopify green
  woocommerce: '#96588A',  // WooCommerce purple
  magento: '#F26822',      // Magento orange
  generic_csv: '#3B82F6',  // Blue for generic CSV
};

// Generate color array for charts
export function generateColors(count: number): string[] {
  const colors = Object.values(CHART_COLORS);
  const result = [];
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length]);
  }
  return result;
}

// Format currency values
export function formatCurrency(value: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

// Format numbers with thousands separator
export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

// Format percentages
export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`;
}

// Format dates for charts
export function formatDate(dateString: string, formatStr: string = 'MMM dd'): string {
  try {
    const date = parseISO(dateString);
    return format(date, formatStr);
  } catch (error) {
    return dateString;
  }
}

// Transform data for pie charts
export function transformForPieChart(data: Array<{name: string; value: number}>) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  return data.map((item, index) => ({
    ...item,
    percentage: (item.value / total) * 100,
    color: generateColors(data.length)[index],
  }));
}

// Transform data for bar charts
export function transformForBarChart(data: Array<{name: string; value: number}>) {
  return data.map((item, index) => ({
    ...item,
    fill: generateColors(data.length)[index],
  }));
}

// Transform data for line charts
export function transformForLineChart(data: Array<{date: string; value: number}>) {
  return data
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map(item => ({
      ...item,
      formattedDate: formatDate(item.date),
    }));
}

// Calculate growth percentage
export function calculateGrowth(current: number, previous: number): number {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
}

// Get top N items from array
export function getTopItems<T extends {value: number}>(data: T[], n: number = 10): T[] {
  return data
    .sort((a, b) => b.value - a.value)
    .slice(0, n);
}

// Group data by platform
export function groupByPlatform<T extends {platform: string}>(data: T[]): Record<string, T[]> {
  return data.reduce((groups, item) => {
    const platform = item.platform;
    if (!groups[platform]) {
      groups[platform] = [];
    }
    groups[platform].push(item);
    return groups;
  }, {} as Record<string, T[]>);
}

// Calculate platform metrics
export function calculatePlatformMetrics(platformData: Record<string, any[]>) {
  return Object.entries(platformData).map(([platform, data]) => ({
    platform,
    count: data.length,
    total: data.reduce((sum, item) => sum + (item.value || item.total_amount || 0), 0),
    average: data.length > 0 ? data.reduce((sum, item) => sum + (item.value || item.total_amount || 0), 0) / data.length : 0,
  }));
}

// Create tooltip formatter for currency
export const currencyTooltipFormatter = (value: number, name: string) => [
  formatCurrency(value),
  name
];

// Create tooltip formatter for numbers
export const numberTooltipFormatter = (value: number, name: string) => [
  formatNumber(value),
  name
];

// Create tooltip formatter for percentages
export const percentageTooltipFormatter = (value: number, name: string) => [
  formatPercentage(value),
  name
];

// Common chart dimensions
export const CHART_DIMENSIONS = {
  small: { width: '100%', height: 200 },
  medium: { width: '100%', height: 300 },
  large: { width: '100%', height: 400 },
  xlarge: { width: '100%', height: 500 },
};

// Common chart margins
export const CHART_MARGINS = {
  default: { top: 20, right: 30, left: 20, bottom: 5 },
  withLabels: { top: 20, right: 30, left: 40, bottom: 40 },
  large: { top: 40, right: 40, left: 40, bottom: 40 },
};