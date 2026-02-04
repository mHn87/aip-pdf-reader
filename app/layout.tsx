import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "AIP PDF Parser",
  description: "Aeronautical Information Publication PDF Parser",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
