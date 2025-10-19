'use client';

import { useState, useEffect } from 'react';

interface NotificationHealth {
  status: string;
  system_info: {
    recipients_configured: number;
    notification_history: number;
    success_rate: number;
    channels_available: string[];
    templates_loaded: number;
  };
  config_status: {
    email_configured: boolean;
    slack_configured: boolean;
    sms_configured: boolean;
  };
}

interface NotificationStats {
  total_notifications: number;
  successful_notifications: number;
  success_rate: number;
  channel_stats: Record<string, any>;
  priority_stats: Record<string, any>;
  recent_notifications: Array<{
    id: string;
    channel: string;
    status: string;
    created_at: string;
  }>;
}

interface AlertNotificationTest {
  demo_results: any;
  notification_status: {
    notifications_sent: boolean;
    alert_count: number;
    timestamp: string;
    notification_details: string;
  };
}

export default function NotificationTestingPage() {
  const [health, setHealth] = useState<NotificationHealth | null>(null);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  const [alertTest, setAlertTest] = useState<AlertNotificationTest | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      const response = await fetch('http://localhost:8001/v2/notifications/health');
      const data = await response.json();
      setHealth(data);
    } catch (err) {
      setError('Failed to fetch notification health');
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8001/v2/notifications/stats');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError('Failed to fetch notification stats');
    }
  };

  const testNotifications = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/v2/notifications/test', {
        method: 'POST',
      });
      const data = await response.json();
      setAlertTest(data);
      // Refresh stats after test
      await fetchStats();
    } catch (err) {
      setError('Failed to send test notifications');
    } finally {
      setLoading(false);
    }
  };

  const testAlertIntegration = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/v2/alerts/demo-with-notifications');
      const data = await response.json();
      setAlertTest(data);
      // Refresh stats after test
      await fetchStats();
    } catch (err) {
      setError('Failed to test alert integration');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchStats();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sent': return 'bg-green-100 text-green-800 border-green-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              🔔 Multi-Channel Notification System
            </h1>
            <p className="text-gray-600 mt-1">Test and monitor the Week 7 notification system</p>
          </div>
          <div className="bg-green-50 text-green-700 border border-green-200 px-3 py-1 rounded-full text-sm">
            Week 7 - Task 2 Complete
          </div>
        </div>

        {error && (
          <div className="border border-red-200 bg-red-50 p-4 rounded-lg">
            <div className="flex items-center gap-2">
              <span className="text-red-600">⚠️</span>
              <span className="text-red-800">{error}</span>
            </div>
          </div>
        )}

        {/* System Health */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
            📊 System Health
          </h2>
          {health ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">System Status</h4>
                <div className="flex items-center gap-2">
                  <span className="text-green-600">✅</span>
                  <span className="text-green-700 font-medium">{health.status}</span>
                </div>
                <div className="text-sm text-gray-600 space-y-1">
                  <div>Recipients: {health.system_info.recipients_configured}</div>
                  <div>Templates: {health.system_info.templates_loaded}</div>
                  <div>History: {health.system_info.notification_history} notifications</div>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Available Channels</h4>
                <div className="space-y-2">
                  {health.system_info.channels_available.map((channel) => (
                    <div key={channel} className="flex items-center gap-2">
                      <span>
                        {channel === 'email' && '📧'}
                        {channel === 'slack' && '💬'}
                        {channel === 'sms' && '📱'}
                        {channel === 'webhook' && '🔗'}
                      </span>
                      <span className="capitalize">{channel}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Configuration Status</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span>📧</span>
                    <span>Email:</span>
                    <span>{health.config_status.email_configured ? '✅' : '❌'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>💬</span>
                    <span>Slack:</span>
                    <span>{health.config_status.slack_configured ? '✅' : '❌'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>📱</span>
                    <span>SMS:</span>
                    <span>{health.config_status.sms_configured ? '✅' : '❌'}</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">Loading health status...</div>
          )}
        </div>

        {/* Testing Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
              📤 Test Basic Notifications
            </h3>
            <p className="text-gray-600 mb-4">
              Send test notifications to all configured recipients across all channels.
            </p>
            <button 
              onClick={testNotifications} 
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Sending...' : 'Send Test Notifications'}
            </button>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
              🚨 Test Alert Integration
            </h3>
            <p className="text-gray-600 mb-4">
              Generate ML alerts and automatically send notifications for detected issues.
            </p>
            <button 
              onClick={testAlertIntegration} 
              disabled={loading}
              className="w-full bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Processing...' : 'Test Alert → Notification Flow'}
            </button>
          </div>
        </div>

        {/* Test Results */}
        {alertTest && (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              ✅ Test Results
            </h3>
            <div className="space-y-4">
              {alertTest.notification_status && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-green-600">✅</span>
                    <span className="font-medium text-green-800">Notifications Processed</span>
                  </div>
                  <div className="text-sm text-green-700 space-y-1">
                    <div>Status: {alertTest.notification_status.notifications_sent ? 'Sent' : 'Failed'}</div>
                    <div>Alert Count: {alertTest.notification_status.alert_count}</div>
                    <div>Details: {alertTest.notification_status.notification_details}</div>
                    <div>Timestamp: {new Date(alertTest.notification_status.timestamp).toLocaleString()}</div>
                  </div>
                </div>
              )}

              {alertTest.demo_results?.alert_summary && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-blue-600">⚠️</span>
                    <span className="font-medium text-blue-800">Generated Alerts</span>
                  </div>
                  <div className="text-sm text-blue-700 space-y-1">
                    <div>Total Alerts: {alertTest.demo_results.alert_summary.total_alerts}</div>
                    <div>Critical Issues: {alertTest.demo_results.alert_summary.critical_count}</div>
                    <div>Status: {alertTest.demo_results.alert_summary.status}</div>
                    <div>Message: {alertTest.demo_results.alert_summary.message}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Delivery Statistics */}
        {stats && (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              📈 Delivery Statistics
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-900">{stats.total_notifications}</div>
                <div className="text-sm text-gray-600">Total Notifications</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">{stats.successful_notifications}</div>
                <div className="text-sm text-gray-600">Successful</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">{stats.success_rate.toFixed(1)}%</div>
                <div className="text-sm text-gray-600">Success Rate</div>
              </div>
            </div>

            {stats.recent_notifications.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Recent Notifications</h4>
                <div className="space-y-2">
                  {stats.recent_notifications.slice(0, 5).map((notification, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <span>
                          {notification.channel === 'email' && '📧'}
                          {notification.channel === 'slack' && '💬'}
                          {notification.channel === 'sms' && '📱'}
                        </span>
                        <span className="text-sm font-medium">{notification.channel}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded text-xs border ${getStatusColor(notification.status)}`}>
                          {notification.status}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(notification.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-gray-500 text-sm">
          Week 7 Enhanced Notification & Reporting System - Multi-Channel Notification Testing Interface
        </div>
      </div>
    </div>
  );
}