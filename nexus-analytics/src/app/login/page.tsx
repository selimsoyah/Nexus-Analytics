"use client";
import { useState } from 'react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    
    try {
      const res = await fetch('http://localhost:8001/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
      });
      const data = await res.json();
      
      if (res.ok) {
        if (typeof window !== 'undefined') {
          localStorage.setItem('auth_token', data.access_token);
          
          // Get user info to check role
          const meRes = await fetch('http://localhost:8001/me', {
            headers: { Authorization: `Bearer ${data.access_token}` },
          });
          const userData = await meRes.json();
          
          if (meRes.ok) {
            localStorage.setItem('user_role', userData.role);
            
            // Redirect based on role
            if (userData.role === 'admin') {
              window.location.replace('/cross-platform');
            } else {
              window.location.replace('/analytics');
            }
          } else {
            setError('Failed to get user information');
          }
        }
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error - make sure backend is running on port 8001');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Nexus Analytics
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access your analytics dashboard
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="text-red-600 text-sm text-center">{error}</div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>

          <div className="text-sm text-center space-y-2">
            <div>
              <strong>Demo Accounts:</strong>
            </div>
            <div className="text-gray-600 space-y-1">
              <div><strong>Regular User:</strong> user@example.com / password123</div>
              <div><strong>Admin (Cross-Platform Access):</strong> admin@nexusanalytics.com / password123</div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}