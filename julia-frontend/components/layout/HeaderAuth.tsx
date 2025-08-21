"use client";
import React from 'react';
import { Avatar, Button, Dropdown, DropdownItem, DropdownMenu, DropdownTrigger } from '@nextui-org/react';
import { LogOut } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';

export default function HeaderAuth() {
  const { user, logout, loading, isAuthenticated } = useAuth() as any;
  const router = useRouter();

  if (loading) return null;
  if (!isAuthenticated) {
    return (
      <div className="flex items-center gap-2">
        <Button size="sm" color="primary" variant="flat" onPress={() => router.push('/login')}>Login</Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <Dropdown placement="bottom-end">
        <DropdownTrigger>
          <Button variant="light" className="px-2" startContent={<Avatar size="sm" name={user?.name} src={user?.picture} />}>{user?.name || user?.email}</Button>
        </DropdownTrigger>
        <DropdownMenu aria-label="Opciones de usuario">
          <DropdownItem key="role" className="text-xs" isReadOnly color="default">Rol: {user?.role || 'student'}</DropdownItem>
          <DropdownItem key="logout" color="danger" startContent={<LogOut size={14} />} onPress={() => logout()}>Cerrar sesión</DropdownItem>
        </DropdownMenu>
      </Dropdown>
    </div>
  );
}
