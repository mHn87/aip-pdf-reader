"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { FileText, ListPlus, Layers, Library, Menu } from "lucide-react"
import { cn } from "@/components/utils"

const nav = [
  { href: "/", label: "Single parse AIP", icon: FileText },
  { href: "/batch-parse", label: "Batch parse", icon: ListPlus },
  { href: "/jobs", label: "Jobs", icon: Layers },
  { href: "/aips", label: "Parsed AIPs", icon: Library },
]

export function LayoutShell() {
  const pathname = usePathname()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const navLinks = (
    <nav className="flex flex-col gap-1 p-2">
      {nav.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || (href !== "/" && pathname.startsWith(href))
        return (
          <Link
            key={href}
            href={href}
            onClick={() => setDrawerOpen(false)}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              active ? "bg-zinc-800 text-white" : "hover:bg-zinc-800/70 hover:text-white text-zinc-300"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            {label}
          </Link>
        )
      })}
    </nav>
  )

  return (
    <>
      {/* Mobile: menu button + drawer overlay */}
      <div className="fixed left-0 top-0 z-50 flex h-14 w-full items-center gap-2 border-b border-zinc-800 bg-zinc-950 px-4 md:hidden">
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          className="rounded p-2 text-zinc-400 hover:bg-zinc-800 hover:text-white"
          aria-label="Open menu"
        >
          <Menu className="h-6 w-6" />
        </button>
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5 text-white" />
          <span className="font-semibold text-white">AIP Parser</span>
        </div>
      </div>

      {drawerOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/60 md:hidden"
            aria-hidden
            onClick={() => setDrawerOpen(false)}
          />
          <aside
            className="fixed left-0 top-0 z-50 h-full w-56 border-r border-zinc-800 bg-zinc-950 pt-14 md:hidden"
            role="dialog"
            aria-label="Navigation"
          >
            <div className="p-2">{navLinks}</div>
          </aside>
        </>
      )}

      {/* Desktop: fixed sidebar */}
      <aside className="fixed left-0 top-0 z-40 hidden h-screen w-56 border-r border-zinc-800 bg-zinc-950 text-zinc-300 md:block">
        <div className="flex h-14 items-center gap-2 border-b border-zinc-800 px-4">
          <FileText className="h-6 w-6 text-white" />
          <span className="font-semibold text-white">AIP Parser</span>
        </div>
        {navLinks}
      </aside>
    </>
  )
}
