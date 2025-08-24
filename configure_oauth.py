#!/usr/bin/env python3
"""
Script de configuración para Google OAuth
Este script te ayudará a configurar correctamente el OAuth de Google
"""

import os
import json
from pathlib import Path

class OAuthSetup:
    def __init__(self):
        self.env_file = Path('.env')
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Cargar configuración actual del archivo .env"""
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        self.config[key] = value
    
    def update_config(self, key, value):
        """Actualizar una variable de configuración"""
        self.config[key] = value
        self.save_config()
    
    def save_config(self):
        """Guardar la configuración en el archivo .env"""
        lines = []
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                lines = f.readlines()
        
        # Actualizar o agregar las variables
        updated_lines = []
        for line in lines:
            if '=' in line and not line.startswith('#'):
                key = line.split('=', 1)[0]
                if key in self.config:
                    updated_lines.append(f"{key}={self.config[key]}\n")
                    del self.config[key]
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Agregar nuevas variables
        for key, value in self.config.items():
            if not any(line.startswith(f"{key}=") for line in updated_lines):
                updated_lines.append(f"{key}={value}\n")
        
        with open(self.env_file, 'w') as f:
            f.writelines(updated_lines)
    
    def setup_google_oauth(self, client_id=None, client_secret=None, redirect_uri=None):
        """Configurar Google OAuth con los valores proporcionados"""
        print("🔧 Configurando Google OAuth...")
        
        if client_id:
            self.update_config('GOOGLE_CLIENT_ID', client_id)
        
        if client_secret:
            self.update_config('GOOGLE_CLIENT_SECRET', client_secret)
        
        if redirect_uri:
            self.update_config('GOOGLE_REDIRECT_URI', redirect_uri)
        
        # Guardar URIs de respaldo
        current_uri = self.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/callback')
        if 'localhost' in current_uri or '127.0.0.1' in current_uri:
            self.update_config('GOOGLE_REDIRECT_URI_DEV', current_uri)
            self.update_config('GOOGLE_REDIRECT_URI_PROD', 'https://tudominio.com/auth/callback')
        
        self.save_config()
        print("✅ Configuración de OAuth actualizada")
    
    def print_instructions(self):
        """Imprimir instrucciones de configuración"""
        print("\n" + "="*60)
        print("📋 INSTRUCCIONES DE CONFIGURACIÓN GOOGLE OAUTH")
        print("="*60)
        
        print("\n1. Ve a Google Cloud Console:")
        print("   https://console.cloud.google.com")
        
        print("\n2. Crea o selecciona tu proyecto")
        
        print("\n3. Habilita la API de Google+:")
        print("   APIs & Services > Library > Google+ API")
        
        print("\n4. Configura las credenciales OAuth:")
        print("   APIs & Services > Credentials > Create Credentials > OAuth client ID")
        
        print("\n5. Configura los URIs de redirección:")
        
        allowed_uris = [
            "http://localhost:8000/auth/callback",
            "http://localhost:3000/auth/callback", 
            "http://127.0.0.1:8000/auth/callback",
            "https://tudominio.com/auth/callback",
            "http://localhost:8000/api/auth/google/callback/redirect",
            "https://tudominio.com/api/auth/google/callback/redirect"
        ]
        
        for uri in allowed_uris:
            print(f"   - {uri}")
        
        print("\n6. Establece estas variables de entorno:")
        for key, value in self.config.items():
            if 'GOOGLE' in key:
                print(f"   {key}={value}")
        
        print("\n7. Reinicia tu aplicación")
        print("="*60)
    
    def get_status(self):
        """Verificar el estado actual de la configuración"""
        print("\n📊 Estado actual de la configuración:")
        print(f"   Entorno: {os.getenv('ENVIRONMENT', 'development')}")
        print(f"   Redirect URI: {self.config.get('GOOGLE_REDIRECT_URI', 'No configurado')}")
        print(f"   Client ID: {'✅ Configurado' if self.config.get('GOOGLE_CLIENT_ID') else '❌ No configurado'}")
        print(f"   Client Secret: {'✅ Configurado' if self.config.get('GOOGLE_CLIENT_SECRET') else '❌ No configurado'}")

def main():
    setup = OAuthSetup()
    
    print("🛠️  Configurador de OAuth para Educational Library")
    print("="*50)
    
    while True:
        print("\nOpciones:")
        print("1. Ver estado actual")
        print("2. Configurar Google OAuth")
        print("3. Ver instrucciones de configuración")
        print("4. Salir")
        
        choice = input("\nSelecciona una opción (1-4): ").strip()
        
        if choice == '1':
            setup.get_status()
        elif choice == '2':
            client_id = input("Google Client ID: ").strip()
            client_secret = input("Google Client Secret: ").strip()
            redirect_uri = input(f"Redirect URI [{setup.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/callback')}]: ").strip()
            
            if not redirect_uri:
                redirect_uri = setup.config.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/callback')
            
            setup.setup_google_oauth(
                client_id=client_id if client_id else None,
                client_secret=client_secret if client_secret else None,
                redirect_uri=redirect_uri
            )
            print("✅ Configuración completada")
        elif choice == '3':
            setup.print_instructions()
        elif choice == '4':
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    main()