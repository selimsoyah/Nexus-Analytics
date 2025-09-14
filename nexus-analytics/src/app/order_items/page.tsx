"use client";
import { useEffect, useState } from 'react';
import ProtectedRoute from '../protectedRoute';

export default function OrderItemsPage() {
  const [orderItems, setOrderItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/order_items')
      .then(res => res.json())
      .then(data => {
        setOrderItems(data.order_items);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch order items');
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <ProtectedRoute>
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Order Items</h1>
        <ul className="space-y-2">
          {orderItems.map(item => (
            <li key={item.order_item_id} className="border p-2 rounded">
              <strong>Order #{item.order_id}</strong> - Product: {item.product}<br />
              Quantity: {item.quantity} | Price: ${item.price}
            </li>
          ))}
        </ul>
      </div>
    </ProtectedRoute>
  );
}
