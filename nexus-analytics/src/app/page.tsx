"use client";
import { useEffect, useState } from 'react';
import ProtectedRoute from './protectedRoute';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/customers')
      .then(res => res.json())
      .then(data => {
        setCustomers(data.customers);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch customers');
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <ProtectedRoute>
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Customers</h1>
        <ul className="space-y-2">
          {customers.map(c => (
            <li key={c.customer_id} className="border p-2 rounded">
              <strong>{c.customer_name}</strong> ({c.email})
            </li>
          ))}
        </ul>
      </div>
    </ProtectedRoute>
  );
}
