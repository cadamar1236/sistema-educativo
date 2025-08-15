import React from 'react';
import { Button } from '@nextui-org/react';
import { FaGoogle } from 'react-icons/fa';

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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/google/login`);
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
      startContent={<FaGoogle />}
      onClick={handleGoogleLogin}
      className={`${fullWidth ? 'w-full' : ''} bg-white text-gray-800 border border-gray-300 hover:bg-gray-50`}
    >
      Continuar con Google
    </Button>
  );
};