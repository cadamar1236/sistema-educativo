import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Providers from './providers'
import HeaderAuth from '@/components/layout/HeaderAuth'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Julia - Plataforma Educativa Inteligente',
  description: 'Sistema educativo avanzado con inteligencia artificial para estudiantes, profesores y administradores',
  keywords: ['educación', 'inteligencia artificial', 'aprendizaje', 'estudiantes', 'profesores'],
  authors: [{ name: 'Julia Education Platform' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen flex flex-col">
            <header className="w-full border-b bg-white/60 dark:bg-gray-900/60 backdrop-blur px-4 py-2 flex justify-between items-center">
              <h1 className="text-sm font-semibold">Julia Plataforma</h1>
              <HeaderAuth />
            </header>
            <main className="flex-1">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
