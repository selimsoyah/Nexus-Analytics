'use client';

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
  Bar,
  Legend
} from 'recharts';

interface ForecastChartProps {
  historicalData: Array<{
    date: string;
    actual: number;
  }>;
  forecastData: Array<{
    date: string;
    forecast: number;
    lower_bound?: number;
    upper_bound?: number;
  }>;
  title?: string;
  height?: number;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  historicalData,
  forecastData,
  title = "Revenue Forecast",
  height = 400
}) => {
  // Combine and prepare data for visualization
  const chartData = React.useMemo(() => {
    interface ChartDataPoint {
      date: string;
      actual: number | null;
      forecast: number | null;
      lower_bound: number | null;
      upper_bound: number | null;
      type: 'historical' | 'forecast';
    }
    
    const combined: ChartDataPoint[] = [];
    
    // Add historical data
    historicalData.forEach(item => {
      combined.push({
        date: item.date,
        actual: item.actual,
        forecast: null,
        lower_bound: null,
        upper_bound: null,
        type: 'historical'
      });
    });
    
    // Add forecast data
    forecastData.forEach(item => {
      combined.push({
        date: item.date,
        actual: null,
        forecast: item.forecast,
        lower_bound: item.lower_bound || null,
        upper_bound: item.upper_bound || null,
        type: 'forecast'
      });
    });
    
    return combined.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [historicalData, forecastData]);

  const formatCurrency = (value: number) => {
    if (value == null) return '';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow border">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            interval="preserveStartEnd"
          />
          <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
          <Tooltip 
            formatter={(value, name) => [
              value ? formatCurrency(Number(value)) : null,
              name === 'actual' ? 'Actual Revenue' : 
              name === 'forecast' ? 'Forecast' : 
              name === 'lower_bound' ? 'Lower Bound' :
              name === 'upper_bound' ? 'Upper Bound' : name
            ]}
            labelFormatter={(label) => `Date: ${formatDate(label)}`}
          />
          <Legend />
          
          {/* Confidence interval area */}
          <Area
            type="monotone"
            dataKey="upper_bound"
            stroke="none"
            fill="#E3F2FD"
            fillOpacity={0.3}
            connectNulls={false}
          />
          <Area
            type="monotone"
            dataKey="lower_bound"
            stroke="none"
            fill="#FFFFFF"
            fillOpacity={1}
            connectNulls={false}
          />
          
          {/* Historical data line */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#2196F3"
            strokeWidth={2}
            dot={{ fill: '#2196F3', strokeWidth: 2, r: 4 }}
            connectNulls={false}
          />
          
          {/* Forecast line */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#FF9800"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: '#FF9800', strokeWidth: 2, r: 4 }}
            connectNulls={false}
          />
          
          {/* Reference line to separate historical and forecast */}
          {historicalData.length > 0 && (
            <ReferenceLine 
              x={historicalData[historicalData.length - 1].date} 
              stroke="#666" 
              strokeDasharray="2 2" 
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
      
      <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-blue-500 mr-2"></div>
          <span>Historical Data</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-orange-500 border-dashed mr-2" style={{borderTopStyle: 'dashed'}}></div>
          <span>Forecast</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-3 bg-blue-100 border border-blue-200 mr-2"></div>
          <span>Confidence Interval</span>
        </div>
      </div>
    </div>
  );
};

interface TrendAnalysisChartProps {
  trendData: Array<{
    period: string;
    revenue: number;
    growth_rate?: number;
  }>;
  title?: string;
  height?: number;
}

export const TrendAnalysisChart: React.FC<TrendAnalysisChartProps> = ({
  trendData,
  title = "Revenue Trends",
  height = 300
}) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow border">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={trendData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis 
            yAxisId="revenue"
            orientation="left"
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} 
          />
          <YAxis 
            yAxisId="growth"
            orientation="right"
            tickFormatter={(value) => `${value.toFixed(1)}%`}
          />
          <Tooltip 
            formatter={(value, name) => [
              name === 'revenue' ? formatCurrency(Number(value)) : `${Number(value).toFixed(2)}%`,
              name === 'revenue' ? 'Revenue' : 'Growth Rate'
            ]}
          />
          <Legend />
          
          <Bar 
            yAxisId="revenue"
            dataKey="revenue" 
            fill="#2196F3" 
            fillOpacity={0.7}
            name="Revenue"
          />
          
          {trendData.some(d => d.growth_rate !== undefined) && (
            <Line
              yAxisId="growth"
              type="monotone"
              dataKey="growth_rate"
              stroke="#FF9800"
              strokeWidth={2}
              dot={{ fill: '#FF9800', strokeWidth: 2, r: 4 }}
              name="Growth Rate"
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

interface SeasonalityChartProps {
  weeklyData: Record<string, { avg_revenue: number }>;
  monthlyData: Record<string, { avg_revenue: number }>;
  title?: string;
}

export const SeasonalityChart: React.FC<SeasonalityChartProps> = ({
  weeklyData,
  monthlyData,
  title = "Seasonal Patterns"
}) => {
  const [viewType, setViewType] = useState<'weekly' | 'monthly'>('weekly');

  // Prepare weekly data
  const weeklyChartData = Object.entries(weeklyData).map(([day, data]) => ({
    period: day,
    avg_revenue: data.avg_revenue
  }));

  // Prepare monthly data
  const monthlyChartData = Object.entries(monthlyData).map(([month, data]) => ({
    period: month,
    avg_revenue: data.avg_revenue
  }));

  const chartData = viewType === 'weekly' ? weeklyChartData : monthlyChartData;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        <div className="flex rounded-md shadow-sm">
          <button
            onClick={() => setViewType('weekly')}
            className={`px-3 py-1 text-sm font-medium rounded-l-md border ${
              viewType === 'weekly'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            Weekly
          </button>
          <button
            onClick={() => setViewType('monthly')}
            className={`px-3 py-1 text-sm font-medium rounded-r-md border-l-0 border ${
              viewType === 'monthly'
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            Monthly
          </button>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
          <Tooltip 
            formatter={(value) => [formatCurrency(Number(value)), 'Average Revenue']}
          />
          
          <Bar 
            dataKey="avg_revenue" 
            fill="#4CAF50" 
            fillOpacity={0.8}
          />
        </ComposedChart>
      </ResponsiveContainer>
      
      <div className="mt-4">
        <p className="text-sm text-gray-600">
          {viewType === 'weekly' 
            ? 'Shows average daily revenue by day of the week'
            : 'Shows average daily revenue by month of the year'
          }
        </p>
      </div>
    </div>
  );
};

interface AccuracyMetricsProps {
  metrics: {
    mae: number;
    mape: number;
    rmse: number;
    r2_score: number;
  };
  modelName: string;
}

export const AccuracyMetrics: React.FC<AccuracyMetricsProps> = ({
  metrics,
  modelName
}) => {
  const getScoreColor = (score: number, type: 'error' | 'accuracy') => {
    if (type === 'error') {
      // Lower is better for error metrics
      if (score < 10) return 'text-green-600';
      if (score < 25) return 'text-yellow-600';
      return 'text-red-600';
    } else {
      // Higher is better for accuracy metrics
      if (score > 0.8) return 'text-green-600';
      if (score > 0.6) return 'text-yellow-600';
      return 'text-red-600';
    }
  };

  const getScoreInterpretation = (score: number, type: 'error' | 'accuracy') => {
    if (type === 'error') {
      if (score < 10) return 'Excellent';
      if (score < 25) return 'Good';
      return 'Needs Improvement';
    } else {
      if (score > 0.8) return 'Excellent';
      if (score > 0.6) return 'Good';
      return 'Fair';
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow border">
      <h3 className="text-lg font-semibold mb-4">
        {modelName} Model Accuracy
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">
            ${metrics.mae.toFixed(0)}
          </div>
          <div className="text-sm text-gray-600 mb-1">MAE</div>
          <div className={`text-xs ${getScoreColor(metrics.mae, 'error')}`}>
            {getScoreInterpretation(metrics.mae, 'error')}
          </div>
        </div>
        
        <div className="text-center">
          <div className={`text-2xl font-bold ${getScoreColor(metrics.mape, 'error')}`}>
            {metrics.mape.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600 mb-1">MAPE</div>
          <div className={`text-xs ${getScoreColor(metrics.mape, 'error')}`}>
            {getScoreInterpretation(metrics.mape, 'error')}
          </div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">
            ${metrics.rmse.toFixed(0)}
          </div>
          <div className="text-sm text-gray-600 mb-1">RMSE</div>
          <div className={`text-xs ${getScoreColor(metrics.rmse, 'error')}`}>
            {getScoreInterpretation(metrics.rmse, 'error')}
          </div>
        </div>
        
        <div className="text-center">
          <div className={`text-2xl font-bold ${getScoreColor(metrics.r2_score, 'accuracy')}`}>
            {(metrics.r2_score * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600 mb-1">R²</div>
          <div className={`text-xs ${getScoreColor(metrics.r2_score, 'accuracy')}`}>
            {getScoreInterpretation(metrics.r2_score, 'accuracy')}
          </div>
        </div>
      </div>
      
      <div className="mt-4 p-3 bg-gray-50 rounded text-sm">
        <p className="text-gray-700">
          <strong>MAE:</strong> Mean Absolute Error - Average prediction error<br/>
          <strong>MAPE:</strong> Mean Absolute Percentage Error - Relative accuracy<br/>
          <strong>RMSE:</strong> Root Mean Square Error - Overall prediction quality<br/>
          <strong>R²:</strong> Coefficient of determination - Model fit quality
        </p>
      </div>
    </div>
  );
};

export default {
  ForecastChart,
  TrendAnalysisChart,
  SeasonalityChart,
  AccuracyMetrics
};