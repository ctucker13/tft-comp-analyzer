import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TFT Composition Analyzer',
  description: 'AI-powered strategic analysis for Teamfight Tactics Set 15: K.O. Coliseum',
  keywords: ['TFT', 'Teamfight Tactics', 'strategy', 'AI', 'analysis', 'compositions'],
  authors: [{ name: 'TFT Analyzer Team' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <div className="min-h-screen bg-gradient-to-br from-tft-dark via-tft-blue to-tft-dark">
          {children}
        </div>
      </body>
    </html>
  )
}