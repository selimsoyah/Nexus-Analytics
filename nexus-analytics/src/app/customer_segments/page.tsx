"use client";
import { useEffect, useState } from 'react';
import ProtectedRoute from '../protectedRoute';

export default function CustomerSegmentsPage() {
  const [segments, setSegments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/customer_segments')
      .then(res => res.json())
      .then(data => {
        setSegments(data.customer_segments);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch customer segments');
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <ProtectedRoute>
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Customer Segments</h1>
        <ul className="space-y-2">
          {segments.map(seg => (
            <li key={seg.customer_id} className="border p-2 rounded">
              <strong>{seg.customer_name}</strong> ({seg.email})<br />
              Total Sales: ${seg.order_total} | Segment: <span className="font-semibold">{seg.segment}</span>
            </li>
          ))}
        </ul>
      </div>
    </ProtectedRoute>
  );
}
