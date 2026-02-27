import type { Metadata } from "next"
import "./globals.css"
import { LayoutShell } from "@/components/LayoutShell"

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
    <html lang="en" className="dark">
      <body className="min-h-screen bg-zinc-950 text-zinc-100">
        <LayoutShell />
        <main className="pt-14 pl-0 md:pt-0 md:pl-56">{children}</main>
      </body>
    </html>
  )
}
