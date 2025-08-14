'use client'

import React from 'react'
import { NextUIProvider } from '@nextui-org/react'
import { ThemeProvider as NextThemesProvider } from 'next-themes'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <NextUIProvider>
      <NextThemesProvider attribute="class" defaultTheme="light" themes={['light', 'dark', 'julia-light', 'julia-dark']}>
        {children}
      </NextThemesProvider>
    </NextUIProvider>
  )
}
