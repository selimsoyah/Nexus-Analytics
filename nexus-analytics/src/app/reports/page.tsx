'use client'

import { useState, useEffect } from 'react'

interface TestReportSummary {
  report_id: string
  title: string
  sections_count: number
  insights_count: number
  record_count: number
  generated_at: string
}

interface TestSampleData {
  executive_summary: string
  key_insights: string[]
  sections: Array<{
    title: string
    type: string
  }>
}

interface TestReportResponse {
  success: boolean
  message: string
  report_summary: TestReportSummary
  sample_data: TestSampleData
}

interface DetailedReportData {
  title: string
  executive_summary: string
  key_insights: string[]
  total_revenue?: number
  total_orders?: number
  avg_order_value?: number
}

interface DetailedReportResponse {
  success: boolean
  report_id: string
  message: string
  data: DetailedReportData
  generated_at: string
}

// Unified interface for display
interface UnifiedReportResponse {
  success: boolean
  title: string
  report_id: string
  message: string
  executive_summary: string
  key_insights: string[]
  generated_at: string
  record_count?: number
  sections_count?: number
  insights_count?: number
  sections?: Array<{ title: string; type: string }>
  isDetailed: boolean
}

interface HealthStatus {
  status: string
  system_info: {
    total_reports_generated: number
    reports_today: number
    database_connected: boolean
    available_report_types: string[]
    supported_formats: string[]
  }
  capabilities: {
    daily_sales_reports: boolean
    customer_analytics: boolean
    weekly_business_reports: boolean
    custom_date_ranges: boolean
    automated_scheduling: boolean
    email_delivery: boolean
  }
}

export default function ReportsPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [reportResult, setReportResult] = useState<UnifiedReportResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [isMounted, setIsMounted] = useState(false)
  const [retryCount, setRetryCount] = useState(0)

  // Helper function to convert test response to unified format
  const convertTestResponse = (response: TestReportResponse): UnifiedReportResponse => {
    return {
      success: response.success,
      title: response.report_summary.title,
      report_id: response.report_summary.report_id,
      message: response.message,
      executive_summary: response.sample_data.executive_summary,
      key_insights: response.sample_data.key_insights,
      generated_at: response.report_summary.generated_at,
      record_count: response.report_summary.record_count,
      sections_count: response.report_summary.sections_count,
      insights_count: response.report_summary.insights_count,
      sections: response.sample_data.sections,
      isDetailed: false
    }
  }

  // Helper function to convert detailed response to unified format
  const convertDetailedResponse = (response: DetailedReportResponse): UnifiedReportResponse => {
    return {
      success: response.success,
      title: response.data.title,
      report_id: response.report_id,
      message: response.message,
      executive_summary: response.data.executive_summary,
      key_insights: response.data.key_insights,
      generated_at: response.generated_at,
      record_count: response.data.total_orders || 0,
      sections_count: 1, // Default for detailed reports
      insights_count: response.data.key_insights.length,
      isDetailed: true
    }
  }

  useEffect(() => {
    setIsMounted(true)
  }, [])

  // Separate effect for health check after mounting
  useEffect(() => {
    if (!isMounted) return
    
    console.log('🚀 Starting initial health check...')
    
    // Add a small delay to ensure the component is fully mounted
    const initialTimer = setTimeout(() => {
      checkSystemHealth()
    }, 500)
    
    return () => clearTimeout(initialTimer)
  }, [isMounted])

  // Auto-retry effect
  useEffect(() => {
    if (isMounted && !healthStatus && error && retryCount < 2) {
      console.log(`🔄 Auto-retry ${retryCount + 1}/2 in 3 seconds...`)
      const retryTimer = setTimeout(() => {
        setRetryCount(prev => prev + 1)
        checkSystemHealth()
      }, 3000)
      
      return () => clearTimeout(retryTimer)
    }
  }, [error, healthStatus, retryCount])

  const checkSystemHealth = async () => {
    try {
      console.log('🔍 Starting health check...')
      
      // Clear any existing errors
      setError(null)
      
      // Add timeout to prevent infinite loading
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 8000) // 8 second timeout
      
      const response = await fetch('http://localhost:8001/v2/reports/health', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
        cache: 'no-cache' // Prevent caching issues
      })
      
      clearTimeout(timeoutId)
      console.log('📡 Health check response status:', response.status)
      
      if (response.ok) {
        const health = await response.json()
        console.log('✅ Health data received:', health)
        setHealthStatus(health)
        setError(null) // Clear any previous errors
      } else {
        const errorText = await response.text()
        console.error('❌ Health check failed:', response.status, errorText)
        setError(`Report system health check failed (${response.status}): ${errorText}`)
      }
    } catch (err) {
      console.error('🚨 Health check error:', err)
      if (err instanceof Error && err.name === 'AbortError') {
        setError('Health check timed out - please try the refresh button')
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error'
        setError(`Failed to connect to report system: ${errorMessage}`)
      }
    }
  }

  const generateReport = async (reportType: string) => {
    setIsLoading(true)
    setError(null)
    setReportResult(null)

    try {
      const response = await fetch(`http://localhost:8001/v2/reports/test?report_type=${reportType}`)
      
      if (response.ok) {
        const result: TestReportResponse = await response.json()
        const unifiedResult = convertTestResponse(result)
        setReportResult(unifiedResult)
        setActiveTab('results')
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Report generation failed')
      }
    } catch (err) {
      setError('Failed to generate report')
    } finally {
      setIsLoading(false)
    }
  }

  const generateDetailedReport = async (reportType: string) => {
    setIsLoading(true)
    setError(null)
    setReportResult(null)

    try {
      let endpoint = ''
      switch (reportType) {
        case 'daily_sales':
          endpoint = '/v2/reports/daily-sales'
          break
        case 'customer_analytics':
          endpoint = '/v2/reports/customer-analytics'
          break
        case 'weekly_business':
          endpoint = '/v2/reports/weekly-business'
          break
        default:
          throw new Error('Unknown report type')
      }

      const response = await fetch(`http://localhost:8001${endpoint}`)
      
      if (response.ok) {
        const result: DetailedReportResponse = await response.json()
        const unifiedResult = convertDetailedResponse(result)
        setReportResult(unifiedResult)
        setActiveTab('results')
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Report generation failed')
      }
    } catch (err) {
      setError('Failed to generate detailed report')
    } finally {
      setIsLoading(false)
    }
  }

  const exportReport = async (format: string = 'pdf') => {
    if (!reportResult) return

    try {
      const exportData = {
        report_data: {
          title: reportResult.title,
          report_id: reportResult.report_id,
          generated_at: reportResult.generated_at,
          executive_summary: reportResult.executive_summary,
          key_insights: reportResult.key_insights,
          record_count: reportResult.record_count,
          sections_count: reportResult.sections_count,
          isDetailed: reportResult.isDetailed
        },
        format: format,
        filename: `${reportResult.title.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}`
      }

      const response = await fetch('http://localhost:8001/v2/reports/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportData)
      })

      if (response.ok) {
        // Create download link
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = exportData.filename + '.' + format
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        setError('Export failed')
      }
    } catch (err) {
      setError('Export failed')
    }
  }

  const emailReport = async () => {
    if (!reportResult) return

    const email = prompt('Enter email address:')
    if (!email) return

    try {
      const emailData = {
        report_data: {
          title: reportResult.title,
          report_id: reportResult.report_id,
          generated_at: reportResult.generated_at,
          executive_summary: reportResult.executive_summary,
          key_insights: reportResult.key_insights,
          record_count: reportResult.record_count,
          sections_count: reportResult.sections_count,
          isDetailed: reportResult.isDetailed
        },
        recipients: [email],
        subject: `📊 ${reportResult.title}`,
        format: 'pdf'
      }

      const response = await fetch('http://localhost:8001/v2/reports/email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(emailData)
      })

      if (response.ok) {
        const result = await response.json()
        alert(`Report scheduled for email delivery to ${email}`)
      } else {
        setError('Email scheduling failed')
      }
    } catch (err) {
      setError('Email scheduling failed')
    }
  }

  if (!isMounted) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 Automated Report Generation</h1>
            <p className="text-gray-600">Loading report system...</p>
          </div>
          <div className="flex items-center justify-center p-8">
            <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Initializing...</span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 Automated Report Generation</h1>
          <p className="text-gray-600">AI-powered business intelligence reports with automated insights</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`${activeTab === 'dashboard' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
              >
                System Dashboard
              </button>
              <button
                onClick={() => setActiveTab('generate')}
                className={`${activeTab === 'generate' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
              >
                Generate Reports
              </button>
              <button
                onClick={() => setActiveTab('results')}
                className={`${activeTab === 'results' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
              >
                Report Results
              </button>
              <button
                onClick={() => setActiveTab('schedule')}
                className={`${activeTab === 'schedule' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'} whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm`}
              >
                Schedule & History
              </button>
            </nav>
          </div>

          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              <div className="bg-white shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <h3 className="text-lg leading-6 font-medium text-gray-900">📈 Report System Status</h3>
                      <p className="text-sm text-gray-500">Real-time status of the automated report generation system</p>
                    </div>
                    <button
                      onClick={() => {
                        setRetryCount(0) // Reset retry count
                        setError(null)   // Clear previous errors
                        checkSystemHealth()
                      }}
                      className="bg-blue-600 text-white px-3 py-1 rounded-md text-sm hover:bg-blue-700 disabled:opacity-50"
                      disabled={!isMounted}
                    >
                      🔄 Refresh Status
                    </button>
                  </div>
                  
                  {healthStatus ? (
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <div className="flex items-center">
                            <div className="flex-shrink-0">
                              <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                              </svg>
                            </div>
                            <div className="ml-3">
                              <p className="text-sm font-medium text-green-900">Total Reports</p>
                              <p className="text-2xl font-bold text-green-700">{healthStatus.system_info.total_reports_generated}</p>
                            </div>
                          </div>
                        </div>

                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <div className="flex items-center">
                            <div className="flex-shrink-0">
                              <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                              </svg>
                            </div>
                            <div className="ml-3">
                              <p className="text-sm font-medium text-blue-900">Reports Today</p>
                              <p className="text-2xl font-bold text-blue-700">{healthStatus.system_info.reports_today}</p>
                            </div>
                          </div>
                        </div>

                        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                          <div className="flex items-center">
                            <div className="flex-shrink-0">
                              <svg className={`h-8 w-8 ${healthStatus.system_info.database_connected ? 'text-green-600' : 'text-red-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                              </svg>
                            </div>
                            <div className="ml-3">
                              <p className="text-sm font-medium text-purple-900">Database</p>
                              <p className="text-lg font-bold text-purple-700">
                                {healthStatus.system_info.database_connected ? 'Connected' : 'Disconnected'}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-white border border-gray-200 rounded-lg p-4">
                          <h4 className="text-lg font-medium mb-3">Available Report Types</h4>
                          <div className="space-y-2">
                            {healthStatus.system_info.available_report_types.map((type) => (
                              <div key={type} className="flex items-center justify-between">
                                <span className="text-sm capitalize">{type.replace('_', ' ')}</span>
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Available
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-lg p-4">
                          <h4 className="text-lg font-medium mb-3">System Capabilities</h4>
                          <div className="space-y-2">
                            {Object.entries(healthStatus.capabilities).map(([key, value]) => (
                              <div key={key} className="flex items-center justify-between">
                                <span className="text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                                <svg className={`h-4 w-4 ${value ? 'text-green-600' : 'text-red-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  {value ? (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                  ) : (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  )}
                                </svg>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="flex items-center justify-center p-8">
                        <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <div className="text-center">
                          <span>Loading system status...</span>
                          {retryCount > 0 && (
                            <p className="text-xs text-gray-500 mt-1">
                              Retry attempt {retryCount}/2
                            </p>
                          )}
                        </div>
                      </div>
                      
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">🔧 Debug Information</h4>
                        <div className="text-xs text-gray-600 space-y-1">
                          <div>Frontend URL: {typeof window !== 'undefined' ? window.location.origin : 'SSR'}</div>
                          <div>Backend URL: http://localhost:8001</div>
                          <div>Mounted: {isMounted ? 'Yes' : 'No'}</div>
                          <div>Check console for network errors</div>
                          <div className="mt-2">
                            <button 
                              onClick={() => {
                                console.log('Manual health check triggered from debug section')
                                setRetryCount(0)
                                setError(null)
                                checkSystemHealth()
                              }}
                              className="bg-gray-600 text-white px-2 py-1 rounded text-xs hover:bg-gray-700"
                            >
                              🔄 Retry Connection
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'generate' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white shadow rounded-lg hover:shadow-lg transition-shadow">
                  <div className="px-4 py-5 sm:p-6">
                    <div className="flex items-center mb-3">
                      <svg className="h-6 w-6 text-green-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                      </svg>
                      <h3 className="text-lg font-medium text-gray-900">Daily Sales Report</h3>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      Comprehensive daily sales performance analysis with AI insights
                    </p>
                    <div className="space-y-2">
                      <button 
                        onClick={() => generateReport('daily_sales')} 
                        disabled={isLoading}
                        className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                      >
                        {isLoading ? 'Generating...' : 'Generate Test Report'}
                      </button>
                      <button 
                        onClick={() => generateDetailedReport('daily_sales')} 
                        disabled={isLoading}
                        className="w-full bg-white border text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 disabled:opacity-50"
                      >
                        Generate Detailed Report
                      </button>
                    </div>
                  </div>
                </div>

                <div className="bg-white shadow rounded-lg hover:shadow-lg transition-shadow">
                  <div className="px-4 py-5 sm:p-6">
                    <div className="flex items-center mb-3">
                      <svg className="h-6 w-6 text-blue-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                      </svg>
                      <h3 className="text-lg font-medium text-gray-900">Customer Analytics</h3>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      Deep customer segmentation and behavior analysis
                    </p>
                    <div className="space-y-2">
                      <button 
                        onClick={() => generateReport('customer_analytics')} 
                        disabled={isLoading}
                        className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                      >
                        {isLoading ? 'Generating...' : 'Generate Test Report'}
                      </button>
                      <button 
                        onClick={() => generateDetailedReport('customer_analytics')} 
                        disabled={isLoading}
                        className="w-full bg-white border text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 disabled:opacity-50"
                      >
                        Generate Detailed Report
                      </button>
                    </div>
                  </div>
                </div>

                <div className="bg-white shadow rounded-lg hover:shadow-lg transition-shadow">
                  <div className="px-4 py-5 sm:p-6">
                    <div className="flex items-center mb-3">
                      <svg className="h-6 w-6 text-purple-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                      <h3 className="text-lg font-medium text-gray-900">Weekly Business Intelligence</h3>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      Comprehensive weekly performance and trend analysis
                    </p>
                    <div className="space-y-2">
                      <button 
                        onClick={() => generateReport('weekly_business')} 
                        disabled={isLoading}
                        className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                      >
                        {isLoading ? 'Generating...' : 'Generate Test Report'}
                      </button>
                      <button 
                        onClick={() => generateDetailedReport('weekly_business')} 
                        disabled={isLoading}
                        className="w-full bg-white border text-gray-700 px-4 py-2 rounded-md hover:bg-gray-50 disabled:opacity-50"
                      >
                        Generate Detailed Report
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'results' && (
            <div className="space-y-6">
              {reportResult ? (
                <div className="bg-white shadow rounded-lg">
                  <div className="px-4 py-5 sm:p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-medium text-gray-900">{reportResult.title}</h3>
                        <p className="text-sm text-gray-600">{reportResult.message}</p>
                        <p className="text-xs text-purple-600 mt-1">
                          {reportResult.isDetailed ? '🔍 Detailed Report' : '⚡ Test Report'}
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        <div className="relative group">
                          <button 
                            onClick={() => exportReport('pdf')}
                            className="bg-white border text-gray-700 px-3 py-1 rounded-md text-sm hover:bg-gray-50"
                          >
                            📥 Export
                          </button>
                          <div className="absolute right-0 mt-1 w-32 bg-white border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                            <button 
                              onClick={() => exportReport('pdf')}
                              className="block w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
                            >
                              📄 PDF
                            </button>
                            <button 
                              onClick={() => exportReport('excel')}
                              className="block w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
                            >
                              📊 Excel
                            </button>
                            <button 
                              onClick={() => exportReport('csv')}
                              className="block w-full text-left px-3 py-2 text-sm hover:bg-gray-50"
                            >
                              📋 CSV
                            </button>
                          </div>
                        </div>
                        <button 
                          onClick={emailReport}
                          className="bg-white border text-gray-700 px-3 py-1 rounded-md text-sm hover:bg-gray-50"
                        >
                          📧 Email
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">Report ID</p>
                        <p className="font-mono text-sm">{reportResult.report_id}</p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">Generated</p>
                        <p className="font-medium">{new Date(reportResult.generated_at).toLocaleString()}</p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">Records Analyzed</p>
                        <p className="text-lg font-bold text-blue-600">{(reportResult.record_count || 0).toLocaleString()}</p>
                      </div>
                      <div className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-sm text-gray-600">Sections & Insights</p>
                        <p className="text-lg font-bold text-purple-600">
                          {reportResult.sections_count || 0}S / {reportResult.insights_count || 0}I
                        </p>
                      </div>
                    </div>

                    {reportResult.executive_summary && (
                      <div className="bg-white border rounded-lg p-4 mb-6">
                        <h4 className="text-lg font-medium mb-3">Executive Summary</h4>
                        <div className="prose max-w-none">
                          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                            {reportResult.executive_summary}
                          </pre>
                        </div>
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-white border rounded-lg p-4">
                        <h4 className="text-lg font-medium mb-3">🔍 Key Insights</h4>
                        <ul className="space-y-2">
                          {reportResult.key_insights.map((insight: string, index: number) => (
                            <li key={index} className="flex items-start space-x-2">
                              <span className="text-blue-600 mt-1">•</span>
                              <span className="text-sm">{insight}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {reportResult.sections && reportResult.sections.length > 0 ? (
                        <div className="bg-white border rounded-lg p-4">
                          <h4 className="text-lg font-medium mb-3">📋 Report Sections</h4>
                          <ul className="space-y-2">
                            {reportResult.sections.map((section: {title: string, type: string}, index: number) => (
                              <li key={index} className="flex items-start space-x-2">
                                <span className="text-green-600 mt-1">→</span>
                                <span className="text-sm">
                                  <strong>{section.title}</strong> ({section.type})
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : (
                        <div className="bg-white border rounded-lg p-4">
                          <h4 className="text-lg font-medium mb-3">📊 Report Type</h4>
                          <div className="flex items-center space-x-2">
                            <span className="text-green-600">✓</span>
                            <span className="text-sm">
                              {reportResult.isDetailed ? 'Comprehensive detailed analysis' : 'Quick overview report'}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white shadow rounded-lg">
                  <div className="px-4 py-8 sm:p-8 text-center">
                    <svg className="h-16 w-16 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Report Generated Yet</h3>
                    <p className="text-gray-600 mb-4">Generate a report from the previous tab to see results here</p>
                    <button 
                      onClick={() => setActiveTab('generate')}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                    >
                      Generate Report
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'schedule' && (
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-2">📅 Report Scheduling & History</h3>
                <p className="text-sm text-gray-500 mb-6">Manage automated report schedules and view generation history</p>
                
                <div className="text-center py-8">
                  <svg className="h-16 w-16 mx-auto text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Scheduling Feature</h4>
                  <p className="text-gray-600 mb-4">
                    Automated report scheduling will be available in the next implementation phase.
                  </p>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    Coming Soon
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}