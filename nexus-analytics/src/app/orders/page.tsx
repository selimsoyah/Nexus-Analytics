"use client";
import { useEffect, useState } from 'react';
import ProtectedRoute from '../protectedRoute';

export default function OrdersPage() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/orders')
      .then(res => res.json())
      .then(data => {
        setOrders(data.orders);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch orders');
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <ProtectedRoute>
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Orders</h1>
        <ul className="space-y-2">
          {orders.map(o => (
            <li key={o.order_id} className="border p-2 rounded">
              <strong>Order #{o.order_id}</strong> - Customer ID: {o.customer_id}<br />
              Date: {o.order_date} | Total: ${o.total}
            </li>
          ))}
        </ul>
      </div>
    </ProtectedRoute>
  );
}
