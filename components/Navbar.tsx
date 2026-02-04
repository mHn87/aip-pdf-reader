import { FileText } from "lucide-react"

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center px-8">
        <div className="flex items-center gap-2">
          <FileText className="h-6 w-6" />
          <span className="font-bold text-lg">AIP PDF Parser</span>
        </div>
        <div className="flex flex-1 items-center justify-end space-x-4">
          <span className="text-sm text-muted-foreground">
            Aeronautical Information Publication Parser
          </span>
        </div>
      </div>
    </nav>
  )
}
