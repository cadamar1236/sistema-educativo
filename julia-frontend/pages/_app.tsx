import type { AppProps } from 'next/app';
import Providers from '@/app/providers';
import '../app/globals.css';

// Wrap all pages/ routes (in the old pages router) with the same Providers used by the app router
// This fixes context errors (useAuthContext debe usarse dentro de AuthProvider) for pages like /auth/callback
export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <Providers>
      <Component {...pageProps} />
    </Providers>
  );
}
