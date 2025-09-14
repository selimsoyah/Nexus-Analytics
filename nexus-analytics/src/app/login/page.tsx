"use client";
import { useState } from 'react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setToken(null);
    setUser(null);
    try {
      const res = await fetch('http://localhost:8000/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
      });
      const data = await res.json();
      if (res.ok) {
        setToken(data.access_token);
        if (typeof window !== 'undefined') {
          localStorage.setItem('token', data.access_token);
          // Redirect after login
          const redirectPath = localStorage.getItem('postLoginRedirect');
          if (redirectPath && redirectPath !== '/login') {
            localStorage.removeItem('postLoginRedirect');
            window.location.replace(redirectPath);
          } else {
            window.location.replace('/'); // Customers page
          }
        }
        // Example: Use token to access protected endpoint
        const meRes = await fetch('http://localhost:8000/me', {
          headers: { Authorization: `Bearer ${data.access_token}` },
        });
        const meData = await meRes.json();
        setUser(meData);
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error');
    }
  };

  return (
    <div className="p-8 max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-4">Login</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block mb-1">Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} className="border p-2 w-full" required />
        </div>
        <div>
          <label className="block mb-1">Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="border p-2 w-full" required />
        </div>
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">Login</button>
      </form>
      {error && <div className="text-red-600 mt-4">{error}</div>}
      {token && (
        <div className="mt-4">
          <div className="text-green-600">Login successful!</div>
          <div className="break-all">Token: {token}</div>
        </div>
      )}
      {user && (
        <div className="mt-4">
          <div className="font-bold">Authenticated User:</div>
          <pre className="bg-gray-100 p-2 rounded text-xs">{JSON.stringify(user, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}