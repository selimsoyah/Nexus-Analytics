"use client";
import { useState } from 'react';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch('http://localhost:8000/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, full_name: fullName, password, role }),
      });
      const data = await res.json();
      if (res.ok) {
        setSuccess(data.msg || 'Registration successful!');
        setUsername('');
        setFullName('');
        setPassword('');
        setRole('user');
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err) {
      setError('Network error');
    }
  };

  return (
    <div className="p-8 max-w-md mx-auto">
      <h1 className="text-2xl font-bold mb-4">Register</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block mb-1">Email</label>
          <input type="email" value={username} onChange={e => setUsername(e.target.value)} className="border p-2 w-full" required />
        </div>
        <div>
          <label className="block mb-1">Full Name</label>
          <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} className="border p-2 w-full" required />
        </div>
        <div>
          <label className="block mb-1">Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="border p-2 w-full" required />
        </div>
        <div>
          <label className="block mb-1">Role</label>
          <select value={role} onChange={e => setRole(e.target.value)} className="border p-2 w-full">
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded">Register</button>
      </form>
      {error && <div className="text-red-600 mt-4">{error}</div>}
      {success && <div className="text-green-600 mt-4">{success}</div>}
    </div>
  );
}
