'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';

const DashboardRedirect: React.FC = () => {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the new unified analytics page
    router.replace('/analytics');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="text-lg mb-2">Redirecting to Analytics Dashboard...</div>
        <div className="text-sm text-gray-600">We've upgraded your dashboard experience!</div>
      </div>
    </div>
  );
};

export default DashboardRedirect;