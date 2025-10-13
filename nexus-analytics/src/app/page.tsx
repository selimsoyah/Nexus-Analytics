'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

const HomePage: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Check if user is already logged in and redirect appropriately
    const token = localStorage.getItem('auth_token');
    const userRole = localStorage.getItem('user_role');
    
    if (token && userRole) {
      if (userRole === 'admin') {
        router.push('/cross-platform');
      } else {
        router.push('/analytics');
      }
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-blue-50">
      <div className="max-w-7xl mx-auto py-16 px-4 sm:py-24 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
            <span className="block">Nexus Analytics</span>
            <span className="block text-indigo-600">Advanced E-commerce Intelligence</span>
          </h1>
          <p className="mt-3 max-w-md mx-auto text-base text-gray-500 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
            Unlock powerful insights from your customer data with AI-powered analytics, 
            advanced segmentation, and predictive intelligence.
          </p>
          
          <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8">
            <div className="rounded-md shadow">
              <Link
                href="/login"
                className="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 md:py-4 md:text-lg md:px-10"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-20">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <div className="pt-6">
              <div className="flow-root bg-white rounded-lg px-6 pb-8">
                <div className="-mt-6">
                  <div>
                    <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                      <div className="text-white text-2xl">🎯</div>
                    </span>
                  </div>
                  <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">
                    Customer Segmentation
                  </h3>
                  <p className="mt-5 text-base text-gray-500">
                    Advanced RFM analysis with 11 intelligent customer segments and ML-powered clustering
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <div className="flow-root bg-white rounded-lg px-6 pb-8">
                <div className="-mt-6">
                  <div>
                    <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                      <div className="text-white text-2xl">💰</div>
                    </span>
                  </div>
                  <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">
                    Customer Lifetime Value
                  </h3>
                  <p className="mt-5 text-base text-gray-500">
                    Predict and optimize customer value with sophisticated CLV calculations and insights
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <div className="flow-root bg-white rounded-lg px-6 pb-8">
                <div className="-mt-6">
                  <div>
                    <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                      <div className="text-white text-2xl">📊</div>
                    </span>
                  </div>
                  <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">
                    Revenue Forecasting
                  </h3>
                  <p className="mt-5 text-base text-gray-500">
                    AI-powered sales predictions and trend analysis for strategic business planning
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <div className="flow-root bg-white rounded-lg px-6 pb-8">
                <div className="-mt-6">
                  <div>
                    <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                      <div className="text-white text-2xl">🤖</div>
                    </span>
                  </div>
                  <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">
                    AI-Powered Insights
                  </h3>
                  <p className="mt-5 text-base text-gray-500">
                    Machine learning algorithms provide actionable recommendations for business growth
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <div className="flow-root bg-white rounded-lg px-6 pb-8">
                <div className="-mt-6">
                  <div>
                    <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                      <div className="text-white text-2xl">🔗</div>
                    </span>
                  </div>
                  <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">
                    Multi-Platform Support
                  </h3>
                  <p className="mt-5 text-base text-gray-500">
                    Universal schema supporting Shopify, WooCommerce, Magento, Amazon, and more
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-6">
              <div className="flow-root bg-white rounded-lg px-6 pb-8">
                <div className="-mt-6">
                  <div>
                    <span className="inline-flex items-center justify-center p-3 bg-indigo-500 rounded-md shadow-lg">
                      <div className="text-white text-2xl">⚡</div>
                    </span>
                  </div>
                  <h3 className="mt-8 text-lg font-medium text-gray-900 tracking-tight">
                    Real-Time Analytics
                  </h3>
                  <p className="mt-5 text-base text-gray-500">
                    Live dashboards with instant insights and real-time performance monitoring
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Demo Accounts */}
        <div className="mt-16 bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-6">Try Demo Accounts</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">👤 Regular User Account</h3>
              <p className="text-gray-600 mb-4">Access customer segmentation and analytics features</p>
              <div className="bg-gray-50 p-3 rounded text-sm">
                <div><strong>Email:</strong> user@example.com</div>
                <div><strong>Password:</strong> password123</div>
              </div>
            </div>
            
            <div className="border border-indigo-200 rounded-lg p-6 bg-indigo-50">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">👑 Admin Account</h3>
              <p className="text-gray-600 mb-4">Full access including cross-platform analytics</p>
              <div className="bg-white p-3 rounded text-sm border">
                <div><strong>Email:</strong> admin@nexusanalytics.com</div>
                <div><strong>Password:</strong> password123</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
