"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { FileText, ListPlus, Layers, Library } from "lucide-react"
import { cn } from "@/components/utils"

const nav = [
  { href: "/", label: "Single parse AIP", icon: FileText },
  { href: "/batch-parse", label: "Batch parse", icon: ListPlus },
  { href: "/jobs", label: "Jobs", icon: Layers },
  { href: "/aips", label: "Parsed AIPs", icon: Library },
]

export function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-56 border-r border-zinc-800 bg-zinc-950 text-zinc-300">
      <div className="flex h-14 items-center gap-2 border-b border-zinc-800 px-4">
        <FileText className="h-6 w-6 text-white" />
        <span className="font-semibold text-white">AIP Parser</span>
      </div>
      <nav className="flex flex-col gap-1 p-2">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href))
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                active ? "bg-zinc-800 text-white" : "hover:bg-zinc-800/70 hover:text-white"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
