import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Providers } from './providers'

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
          {children}
        </Providers>
      </body>
    </html>
  )
}
