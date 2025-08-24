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
			try { 
				localStorage.setItem('auth_redirect', '/dashboard'); 
				// Auto redirect to login after a short delay
				setTimeout(() => router.push('/login'), 2000);
			} catch {}
		}
		return (
			<div className="p-8 text-center">
				<div className="max-w-md mx-auto">
					<h2 className="text-xl font-semibold mb-2">Acceso Requerido</h2>
					<p className="text-gray-600 mb-4">Debes iniciar sesión para acceder al dashboard.</p>
					<p className="text-sm text-gray-500">Redirigiendo al login...</p>
				</div>
			</div>
		);
	}
	if (user.role === 'teacher') return null; // redirigiendo

		return <StudentDashboard />;
}
