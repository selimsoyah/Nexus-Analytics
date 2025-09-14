"use client";
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (!token && typeof window !== 'undefined') {
      // Save the current path so we can redirect after login
      localStorage.setItem('postLoginRedirect', window.location.pathname);
      router.replace('/login');
    }
  }, [router]);

  return <>{children}</>;
}
