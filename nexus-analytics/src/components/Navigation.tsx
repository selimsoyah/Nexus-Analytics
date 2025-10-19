'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const Navigation: React.FC = () => {
  const [userRole, setUserRole] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setIsMounted(true);
    const token = localStorage.getItem('auth_token');
    const role = localStorage.getItem('user_role');
    
    setIsAuthenticated(!!token);
    setUserRole(role);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_role');
    setIsAuthenticated(false);
    setUserRole(null);
    router.push('/login');
  };

  // Prevent hydration mismatch by not rendering until mounted
  if (!isMounted) {
    return (
      <nav className="bg-indigo-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-white text-xl font-bold">
                Nexus Analytics
              </Link>
            </div>
            <div className="flex items-center">
              <div className="animate-pulse bg-indigo-500 h-4 w-16 rounded"></div>
            </div>
          </div>
        </div>
      </nav>
    );
  }

  if (!isAuthenticated) {
    return (
      <nav className="bg-indigo-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-white text-xl font-bold">
                Nexus Analytics
              </Link>
            </div>
            <div className="flex items-center">
              <Link 
                href="/login" 
                className="text-white hover:text-indigo-200 px-3 py-2 rounded-md text-sm font-medium"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="bg-indigo-600 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-white text-xl font-bold">
              Nexus Analytics
            </Link>
            
            <div className="flex space-x-4">
              <Link 
                href="/analytics" 
                className="text-white hover:text-indigo-200 px-3 py-2 rounded-md text-sm font-medium"
              >
                📊 Analytics Dashboard
              </Link>
              
              <Link 
                href="/segmentation" 
                className="text-white hover:text-indigo-200 px-3 py-2 rounded-md text-sm font-medium"
              >
                🎯 Customer Segmentation
              </Link>
              
              <Link 
                href="/clv" 
                className="text-white hover:text-indigo-200 px-3 py-2 rounded-md text-sm font-medium"
              >
                💰 CLV Analytics
              </Link>
              
              <Link 
                href="/shopify" 
                className="text-white hover:text-indigo-200 px-3 py-2 rounded-md text-sm font-medium"
              >
                🛒 Shopify Integration
              </Link>
              
              <Link 
                href="/reports" 
                className="text-white hover:text-indigo-200 px-3 py-2 rounded-md text-sm font-medium"
              >
                📊 Reports
              </Link>
              
              {userRole === 'admin' && (
                <Link 
                  href="/cross-platform" 
                  className="text-white hover:text-indigo-200 px-3 py-2 rounded-md text-sm font-medium border border-indigo-400 rounded"
                >
                  🔒 Cross-Platform Analytics
                </Link>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <span className="text-indigo-200 text-sm">
              {userRole === 'admin' ? '👑 Admin' : '👤 User'}
            </span>
            <button 
              onClick={handleLogout}
              className="text-white hover:text-indigo-200 px-3 py-2 rounded-md text-sm font-medium"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;