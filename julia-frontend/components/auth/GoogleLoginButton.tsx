import React from 'react';
import { apiBase } from '../../lib/runtimeApi';
import { Button } from '@nextui-org/react';

// Icono de Google inline (evita dependencia de react-icons)
const GoogleIcon: React.FC<{ className?: string }> = ({ className = 'w-4 h-4' }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 488 512"
    className={className}
    aria-hidden="true"
    focusable="false"
  >
    <path fill="#4285F4" d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.9c2.3 12.7 3.1 24.9 3.1 41.4z"/>
  </svg>
);

interface GoogleLoginButtonProps {
  onLogin?: () => void;
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

export const GoogleLoginButton: React.FC<GoogleLoginButtonProps> = ({
  onLogin,
  size = 'md',
  fullWidth = false
}) => {
  const handleGoogleLogin = async () => {
    try {
      // Obtener URL de autenticación del backend
  const response = await fetch(`${apiBase()}/api/auth/google/login`);
      const data = await response.json();
      
      if (data.auth_url) {
        // Redirigir a Google para autenticación
        window.location.href = data.auth_url;
      } else {
        console.error('No se pudo obtener la URL de autenticación');
      }
      
      if (onLogin) {
        onLogin();
      }
    } catch (error) {
      console.error('Error iniciando login con Google:', error);
    }
  };

  return (
    <Button
      color="primary"
      size={size}
      startContent={<GoogleIcon />}
      onClick={handleGoogleLogin}
      className={`${fullWidth ? 'w-full' : ''} bg-white text-gray-800 border border-gray-300 hover:bg-gray-50`}
    >
      Continuar con Google
    </Button>
  );
};