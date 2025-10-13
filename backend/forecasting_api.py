"""
Revenue Forecasting API Endpoints

This module provides REST API endpoints for revenue forecasting functionality:
- Generate revenue forecasts with multiple models
- Analyze seasonal patterns and trends
- Provide forecast accuracy metrics
- Business insights and recommendations

Author: Nexus Analytics Team
Date: October 2025
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Any
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from database import get_database_connection
from auth import get_current_user, get_admin_user
from safe_forecasting import create_safe_forecaster_from_orders, create_async_safe_forecaster_from_orders
# Keep original as fallback
try:
    from analytics.revenue_forecasting import create_forecaster_from_orders, RevenueForecaster, STATSMODELS_AVAILABLE, PROPHET_AVAILABLE
    ORIGINAL_FORECASTING_AVAILABLE = True
except ImportError:
    ORIGINAL_FORECASTING_AVAILABLE = False
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter()


def execute_query(conn, query, params):
    """Helper function to execute database queries with SQLAlchemy"""
    from sqlalchemy import text
    try:
        if params and len(params) > 0:
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))
        
        return [dict(row) for row in result.mappings()]
    except Exception as e:
        logger.error(f"Database query error: {str(e)}")
        return []


def execute_query(conn, query: str, params: list = None) -> List[Dict]:
    """
    Helper function to execute SQL queries using SQLAlchemy
    
    Args:
        conn: SQLAlchemy database connection
        query: SQL query string with ? placeholders
        params: List of parameters for the query
        
    Returns:
        List of dictionaries representing query results
    """
    try:
        # Convert ? placeholders to named parameters for SQLAlchemy
        if params:
            # Replace ? with named parameters
            param_dict = {}
            for i, param in enumerate(params):
                param_name = f"param{i}"
                query = query.replace("?", f":{param_name}", 1)
                param_dict[param_name] = param
            result = conn.execute(text(query), param_dict)
        else:
            result = conn.execute(text(query))
        
        # Convert to list of dictionaries
        return [dict(row) for row in result.mappings()]
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise


@router.get("/forecasting/revenue/forecast")
async def generate_revenue_forecast(
    forecast_periods: int = Query(30, ge=7, le=365, description="Number of days to forecast"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate comprehensive revenue forecast using ensemble models
    
    Returns:
    - Forecast values with confidence intervals
    - Model performance metrics
    - Business insights and recommendations
    """
    try:
        # Get database connection
        conn = get_database_connection()
        
        # Build query - using actual table structure with date casting
        query = """
            SELECT order_id, order_date, total
            FROM orders 
            WHERE order_date::date >= CURRENT_DATE - INTERVAL '2 years'
            ORDER BY order_date::date
        """
        params = []
        
        # Note: Platform filtering not available in current schema
        if platform:
            logger.warning(f"Platform filtering requested ({platform}) but not supported in current schema")
        
        # Execute query using helper function (no params needed)
        orders_data = execute_query(conn, query, [])
        
        # Process each order
        for order_dict in orders_data:
            # Convert date to string if it's a date object
            if hasattr(order_dict.get('order_date'), 'strftime'):
                order_dict['order_date'] = order_dict['order_date'].strftime('%Y-%m-%d')
            
            # Map 'total' to 'total_amount' for forecasting engine compatibility
            if 'total' in order_dict:
                order_dict['total_amount'] = order_dict['total']
        
        conn.close()
        
        if len(orders_data) < 3:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient historical data for forecasting (need at least 3 orders, found {len(orders_data)})"
            )
        
        # Generate forecast report using safe method
        logger.info(f"Generating safe forecast for {len(orders_data)} orders, {forecast_periods} periods")
        
        # Use safe forecasting to prevent crashes
        forecast_report = create_safe_forecaster_from_orders(orders_data, forecast_periods)
        
        if 'error' in forecast_report:
            raise HTTPException(status_code=500, detail=f"Forecasting error: {forecast_report['error']}")
        
        # Add metadata
        forecast_report['metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'forecast_periods': forecast_periods,
            'platform_filter': platform,
            'user_id': current_user.get('username', 'unknown')
        }
        
        return {
            'status': 'success',
            'forecast_report': forecast_report
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating revenue forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/forecasting/revenue/trends")
async def analyze_revenue_trends(
    period: str = Query("monthly", regex="^(daily|weekly|monthly|quarterly)$"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze revenue trends and patterns
    
    Returns:
    - Trend analysis (growth rates, seasonality)
    - Period-over-period comparisons
    - Statistical significance tests
    """
    try:
        conn = get_database_connection()
        
        # Determine grouping based on period
        if period == "daily":
            group_by = "DATE(order_date)"
            date_format = "%Y-%m-%d"
        elif period == "weekly":
            group_by = "DATE(order_date, 'weekday 0', '-6 days')"  # Week starting Monday
            date_format = "%Y-W%W"
        elif period == "monthly":
            group_by = "DATE(order_date, 'start of month')"
            date_format = "%Y-%m"
        else:  # quarterly
            group_by = "DATE(order_date, 'start of month', '-' || ((strftime('%m', order_date) - 1) % 3) || ' months')"
            date_format = "%Y-Q%q"
        
        # Build query
        base_query = f"""
            SELECT 
                {group_by} as period_date,
                SUM(total) as total_revenue,
                COUNT(*) as order_count,
                AVG(total) as avg_order_value
            FROM orders 
            WHERE order_date::date >= CURRENT_DATE - INTERVAL '2 years'
            GROUP BY {group_by} 
            ORDER BY period_date
        """
        
        params = []
        # Platform filtering not supported in current schema
        if platform:
            logger.warning(f"Platform filtering requested ({platform}) but not supported in current schema")
        
        # Execute query using helper function
        trend_data = execute_query(conn, base_query, params)
        
        conn.close()
        
        if len(trend_data) < 3:
            raise HTTPException(
                status_code=400, 
                detail="Insufficient data for trend analysis"
            )
        
        # Calculate trend metrics
        revenues = [item['total_revenue'] for item in trend_data]
        
        # Growth rate calculation
        if len(revenues) >= 2:
            recent_avg = sum(revenues[-3:]) / min(3, len(revenues))
            previous_avg = sum(revenues[:3]) / min(3, len(revenues))
            growth_rate = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
        else:
            growth_rate = 0
        
        # Volatility
        import numpy as np
        volatility = np.std(revenues) / np.mean(revenues) if np.mean(revenues) > 0 else 0
        
        # Trend direction
        if len(revenues) >= 5:
            # Simple linear trend
            x = list(range(len(revenues)))
            correlation = np.corrcoef(x, revenues)[0, 1] if len(revenues) > 1 else 0
            trend_direction = "increasing" if correlation > 0.1 else "decreasing" if correlation < -0.1 else "stable"
        else:
            trend_direction = "insufficient_data"
        
        return {
            'status': 'success',
            'period': period,
            'platform_filter': platform,
            'trend_data': trend_data,
            'trend_analysis': {
                'growth_rate_percent': round(growth_rate, 2),
                'volatility': round(volatility, 3),
                'trend_direction': trend_direction,
                'total_periods': len(trend_data),
                'total_revenue': sum(revenues),
                'avg_period_revenue': sum(revenues) / len(revenues)
            },
            'generated_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing revenue trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/forecasting/revenue/seasonality")
async def analyze_seasonality(
    current_user: dict = Depends(get_current_user),
    platform: Optional[str] = Query(None, description="Filter by platform")
):
    """
    Analyze seasonal patterns in revenue data
    
    Returns:
    - Weekly seasonality patterns
    - Monthly seasonality patterns
    - Holiday effects (if applicable)
    - Seasonal strength metrics
    """
    try:
        conn = get_database_connection()
        
        # Get detailed daily data for seasonality analysis
        query = """
            SELECT 
                order_date,
                SUM(total) as daily_revenue,
                COUNT(*) as daily_orders,
                strftime('%w', order_date) as day_of_week,
                strftime('%m', order_date) as month,
                strftime('%d', order_date) as day_of_month
            FROM orders 
            WHERE order_date::date >= CURRENT_DATE - INTERVAL '1 year'
            GROUP BY order_date 
            ORDER BY order_date
        """
        
        params = []
        # Platform filtering not supported in current schema
        if platform:
            logger.warning(f"Platform filtering requested ({platform}) but not supported in current schema")
        
        # Execute query using helper function
        daily_data = execute_query(conn, query, params)
        
        conn.close()
        
        if len(daily_data) < 90:
            raise HTTPException(
                status_code=400, 
                detail="Insufficient data for seasonality analysis (minimum 90 days required)"
            )
        
        # Weekly seasonality analysis
        weekly_patterns = {}
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        for day in range(7):
            day_data = [item['daily_revenue'] for item in daily_data if int(item['day_of_week']) == day]
            if day_data:
                weekly_patterns[day_names[day]] = {
                    'avg_revenue': sum(day_data) / len(day_data),
                    'total_days': len(day_data),
                    'day_index': day
                }
        
        # Monthly seasonality analysis
        monthly_patterns = {}
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for month in range(1, 13):
            month_data = [item['daily_revenue'] for item in daily_data if int(item['month']) == month]
            if month_data:
                monthly_patterns[month_names[month-1]] = {
                    'avg_revenue': sum(month_data) / len(month_data),
                    'total_days': len(month_data),
                    'month_index': month
                }
        
        # Calculate seasonal strength
        all_revenues = [item['daily_revenue'] for item in daily_data]
        overall_avg = sum(all_revenues) / len(all_revenues)
        
        # Weekly seasonal strength
        weekly_variance = 0
        for pattern in weekly_patterns.values():
            weekly_variance += (pattern['avg_revenue'] - overall_avg) ** 2
        weekly_strength = (weekly_variance / len(weekly_patterns)) / (sum([(r - overall_avg)**2 for r in all_revenues]) / len(all_revenues)) if len(all_revenues) > 0 else 0
        
        # Monthly seasonal strength
        monthly_variance = 0
        for pattern in monthly_patterns.values():
            monthly_variance += (pattern['avg_revenue'] - overall_avg) ** 2
        monthly_strength = (monthly_variance / len(monthly_patterns)) / (sum([(r - overall_avg)**2 for r in all_revenues]) / len(all_revenues)) if len(all_revenues) > 0 else 0
        
        return {
            'status': 'success',
            'platform_filter': platform,
            'analysis_period': {
                'start_date': daily_data[0]['order_date'],
                'end_date': daily_data[-1]['order_date'],
                'total_days': len(daily_data)
            },
            'weekly_seasonality': {
                'patterns': weekly_patterns,
                'strength': round(weekly_strength, 3),
                'strongest_day': max(weekly_patterns.items(), key=lambda x: x[1]['avg_revenue'])[0] if weekly_patterns else None,
                'weakest_day': min(weekly_patterns.items(), key=lambda x: x[1]['avg_revenue'])[0] if weekly_patterns else None
            },
            'monthly_seasonality': {
                'patterns': monthly_patterns,
                'strength': round(monthly_strength, 3),
                'strongest_month': max(monthly_patterns.items(), key=lambda x: x[1]['avg_revenue'])[0] if monthly_patterns else None,
                'weakest_month': min(monthly_patterns.items(), key=lambda x: x[1]['avg_revenue'])[0] if monthly_patterns else None
            },
            'overall_metrics': {
                'avg_daily_revenue': overall_avg,
                'total_revenue': sum(all_revenues)
            },
            'generated_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing seasonality: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/forecasting/revenue/accuracy")
async def forecast_accuracy_metrics(
    current_user: dict = Depends(get_current_user),
    test_periods: int = Query(30, ge=7, le=90, description="Number of recent days to test against"),
    platform: Optional[str] = Query(None, description="Filter by platform")
):
    """
    Calculate forecast accuracy metrics using historical data
    
    Returns:
    - Model performance metrics (MAE, MAPE, RMSE)
    - Backtesting results
    - Model comparison
    """
    try:
        conn = get_database_connection()
        
        # Get historical data (excluding test period)
        query = """
            SELECT order_id, order_date, total
            FROM orders 
            WHERE order_date::date >= CURRENT_DATE - INTERVAL '2 years' 
            AND order_date::date <= CURRENT_DATE - INTERVAL '{} days'
            ORDER BY order_date
        """.format(test_periods)
        
        params = []
        # Platform filtering not supported in current schema
        if platform:
            logger.warning(f"Platform filtering requested ({platform}) but not supported in current schema")
        
        # Execute query using helper function
        historical_orders = execute_query(conn, query, params)
        
        # Process date formatting and column mapping
        for order_dict in historical_orders:
            if hasattr(order_dict.get('order_date'), 'strftime'):
                order_dict['order_date'] = order_dict['order_date'].strftime('%Y-%m-%d')
            
            # Map 'total' to 'total_amount' for forecasting engine compatibility
            if 'total' in order_dict:
                order_dict['total_amount'] = order_dict['total']
        
        # Get actual data for test period
        test_query = """
            SELECT order_date, SUM(total) as actual_revenue
            FROM orders 
            WHERE order_date::date > CURRENT_DATE - INTERVAL '{} days'
            GROUP BY order_date 
            ORDER BY order_date
        """.format(test_periods)
        
        # Platform filtering not supported in current schema
        if platform:
            logger.warning(f"Platform filtering requested ({platform}) but not supported in current schema")
        
        # Execute test query using helper function
        test_results = execute_query(conn, test_query, params)
        actual_test_data = []
        
        for row_dict in test_results:
            actual_test_data.append({
                'date': row_dict['order_date'].strftime('%Y-%m-%d') if hasattr(row_dict.get('order_date'), 'strftime') else row_dict.get('order_date'),
                'actual_revenue': row_dict.get('actual_revenue')
            })
        
        conn.close()
        
        if len(historical_orders) < 60:
            raise HTTPException(
                status_code=400, 
                detail="Insufficient historical data for accuracy testing"
            )
        
        if len(actual_test_data) < test_periods * 0.8:  # Allow some missing days
            raise HTTPException(
                status_code=400, 
                detail="Insufficient actual data for accuracy testing"
            )
        
        # Generate forecast using historical data
        forecaster = RevenueForecaster()
        forecaster.prepare_data(historical_orders)
        
        # Fit models and generate forecast
        arima_result = forecaster.fit_arima_model(forecaster.data['revenue'], test_periods)
        prophet_result = forecaster.fit_prophet_model(forecaster.data, test_periods)
        ensemble_result = forecaster.ensemble_forecast(test_periods)
        
        # Calculate accuracy metrics
        actual_revenues = [item['actual_revenue'] for item in actual_test_data]
        
        accuracy_results = {}
        
        # ARIMA accuracy
        if 'error' not in arima_result:
            arima_forecast = arima_result['forecast'][:len(actual_revenues)]
            arima_accuracy = forecaster.calculate_forecast_accuracy(
                pd.Series(actual_revenues), 
                pd.Series(arima_forecast)
            )
            accuracy_results['arima'] = arima_accuracy
        
        # Prophet accuracy
        if 'error' not in prophet_result:
            prophet_forecast = prophet_result['forecast_values']['yhat'].values[:len(actual_revenues)]
            prophet_accuracy = forecaster.calculate_forecast_accuracy(
                pd.Series(actual_revenues), 
                pd.Series(prophet_forecast)
            )
            accuracy_results['prophet'] = prophet_accuracy
        
        # Ensemble accuracy
        if 'error' not in ensemble_result:
            ensemble_forecast = ensemble_result['forecast'][:len(actual_revenues)]
            ensemble_accuracy = forecaster.calculate_forecast_accuracy(
                pd.Series(actual_revenues), 
                pd.Series(ensemble_forecast)
            )
            accuracy_results['ensemble'] = ensemble_accuracy
        
        # Determine best model
        best_model = None
        best_mape = float('inf')
        
        for model_name, metrics in accuracy_results.items():
            if metrics['mape'] < best_mape:
                best_mape = metrics['mape']
                best_model = model_name
        
        return {
            'status': 'success',
            'test_config': {
                'test_periods': test_periods,
                'platform_filter': platform,
                'historical_data_points': len(historical_orders),
                'actual_test_points': len(actual_test_data)
            },
            'accuracy_metrics': accuracy_results,
            'model_ranking': {
                'best_model': best_model,
                'best_mape': round(best_mape, 2) if best_mape != float('inf') else None
            },
            'actual_vs_forecast': [
                {
                    'date': item['date'],
                    'actual': item['actual_revenue'],
                    'arima_forecast': float(arima_result['forecast'][i]) if 'error' not in arima_result and i < len(arima_result['forecast']) else None,
                    'prophet_forecast': float(prophet_result['forecast_values']['yhat'].iloc[i]) if 'error' not in prophet_result and i < len(prophet_result['forecast_values']) else None,
                    'ensemble_forecast': float(ensemble_result['forecast'][i]) if 'error' not in ensemble_result and i < len(ensemble_result['forecast']) else None
                }
                for i, item in enumerate(actual_test_data)
            ],
            'generated_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating forecast accuracy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/forecasting/revenue/scenarios")
async def revenue_scenarios(
    base_forecast_periods: int = Query(30, ge=7, le=365),
    growth_scenarios: List[float] = Query([0.0, 0.05, 0.10, -0.05], description="Growth rate scenarios"),
    current_user: dict = Depends(get_current_user),
    platform: Optional[str] = Query(None, description="Filter by platform")
):
    """
    Generate what-if revenue scenarios based on different growth assumptions
    
    Returns:
    - Base forecast
    - Multiple growth scenarios
    - Risk analysis
    - Business recommendations
    """
    try:
        conn = get_database_connection()
        
        # Get recent data for baseline
        query = """
            SELECT order_id, order_date, total
            FROM orders 
            WHERE order_date::date >= CURRENT_DATE - INTERVAL '1 year'
            ORDER BY order_date
        """
        
        params = []
        # Platform filtering not supported in current schema
        if platform:
            logger.warning(f"Platform filtering requested ({platform}) but not supported in current schema")
        
        # Execute query using helper function
        orders_data = execute_query(conn, query, params)
        
        # Process date formatting and column mapping
        for order_dict in orders_data:
            if hasattr(order_dict.get('order_date'), 'strftime'):
                order_dict['order_date'] = order_dict['order_date'].strftime('%Y-%m-%d')
            
            # Map 'total' to 'total_amount' for forecasting engine compatibility
            if 'total' in order_dict:
                order_dict['total_amount'] = order_dict['total']
        
        conn.close()
        
        if len(orders_data) < 30:
            raise HTTPException(
                status_code=400, 
                detail="Insufficient data for scenario analysis"
            )
        
        # Generate base forecast
        base_report = create_forecaster_from_orders(orders_data, base_forecast_periods)
        
        if 'error' in base_report:
            raise HTTPException(status_code=500, detail=f"Base forecast error: {base_report['error']}")
        
        base_forecast = base_report.get('ensemble_forecast', {}).get('forecast_values', [])
        
        if not base_forecast:
            raise HTTPException(status_code=500, detail="Unable to generate base forecast")
        
        # Generate scenarios
        scenarios = {}
        
        for growth_rate in growth_scenarios:
            scenario_name = f"growth_{growth_rate:+.1%}".replace('+', 'plus_').replace('-', 'minus_').replace('.', '_')
            
            # Apply growth rate to base forecast
            scenario_forecast = []
            for i, base_value in enumerate(base_forecast):
                # Apply compound growth over the forecast period
                growth_factor = (1 + growth_rate) ** (i / 30)  # Assuming monthly compounding
                scenario_value = base_value * growth_factor
                scenario_forecast.append(scenario_value)
            
            scenarios[scenario_name] = {
                'growth_rate': growth_rate,
                'forecast_values': scenario_forecast,
                'total_forecast': sum(scenario_forecast),
                'vs_base_difference': sum(scenario_forecast) - sum(base_forecast),
                'vs_base_percent': ((sum(scenario_forecast) - sum(base_forecast)) / sum(base_forecast) * 100) if sum(base_forecast) > 0 else 0
            }
        
        # Risk analysis
        scenario_totals = [scenario['total_forecast'] for scenario in scenarios.values()]
        base_total = sum(base_forecast)
        
        risk_analysis = {
            'volatility': np.std(scenario_totals) / np.mean(scenario_totals) if np.mean(scenario_totals) > 0 else 0,
            'upside_potential': max(scenario_totals) - base_total,
            'downside_risk': min(scenario_totals) - base_total,
            'range_percent': ((max(scenario_totals) - min(scenario_totals)) / base_total * 100) if base_total > 0 else 0
        }
        
        # Business recommendations
        recommendations = []
        
        if risk_analysis['upside_potential'] > base_total * 0.1:
            recommendations.append("Significant upside potential identified. Consider aggressive growth strategies.")
        
        if abs(risk_analysis['downside_risk']) > base_total * 0.1:
            recommendations.append("Notable downside risk detected. Implement risk mitigation strategies.")
        
        if risk_analysis['volatility'] > 0.2:
            recommendations.append("High forecast volatility suggests need for flexible resource planning.")
        
        return {
            'status': 'success',
            'base_forecast': {
                'forecast_values': base_forecast,
                'total_forecast': sum(base_forecast),
                'forecast_periods': base_forecast_periods
            },
            'scenarios': scenarios,
            'risk_analysis': {
                'volatility': round(risk_analysis['volatility'], 3),
                'upside_potential': round(risk_analysis['upside_potential'], 2),
                'downside_risk': round(risk_analysis['downside_risk'], 2),
                'range_percent': round(risk_analysis['range_percent'], 2)
            },
            'recommendations': recommendations,
            'metadata': {
                'platform_filter': platform,
                'growth_scenarios_tested': growth_scenarios,
                'generated_at': datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating revenue scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Health check endpoint
@router.get("/forecasting/health")
async def forecasting_health():
    """Health check for forecasting service"""
    try:
        # Test basic functionality
        test_orders = [
            {'order_id': 'test1', 'order_date': '2024-10-01', 'total_amount': 100},
            {'order_id': 'test2', 'order_date': '2024-10-02', 'total_amount': 150}
        ]
        
        forecaster = RevenueForecaster()
        forecaster.prepare_data(test_orders)
        
        return {
            'status': 'healthy',
            'forecasting_engine': 'operational',
            'models_available': {
                'arima': STATSMODELS_AVAILABLE,
                'prophet': PROPHET_AVAILABLE
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }