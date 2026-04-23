import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import '../styles/globals.css'

export const metadata: Metadata = {
  title: 'Studentska Platforma',
  description: 'Platforma za upravljanje univerzitetskim konsultacijama',
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="sr">
      <body>
        <main>
          {children}
        </main>
      </body>
    </html>
  )
}
