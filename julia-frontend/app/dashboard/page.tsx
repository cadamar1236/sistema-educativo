"use client";
import React, { useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import StudentDashboard from '@/components/student/StudentDashboard';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
	const { user, loading } = useAuth() as any;
	const router = useRouter();

	useEffect(() => {
		if (user && user.role === 'teacher') {
			router.replace('/dashboard/teacher');
		}
	}, [user, router]);

	if (loading) return <div className="p-8">Cargando aplicación...</div>;
	if (!user) {
		if (typeof window !== 'undefined') {
			try { localStorage.setItem('auth_redirect', '/dashboard'); } catch {}
		}
		return <div className="p-8">No autenticado.</div>;
	}
	if (user.role === 'teacher') return null; // redirigiendo

		return <StudentDashboard />;
}
