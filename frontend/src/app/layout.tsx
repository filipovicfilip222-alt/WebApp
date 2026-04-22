import type { Metadata } from 'next'
import '../styles/globals.css'

export const metadata: Metadata = {
  title: 'Studentska Platforma',
  description: 'Platforma za upravljanje univerzitetskim konsultacijama',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
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
