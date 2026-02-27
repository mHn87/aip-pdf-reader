import { Loader2 } from "lucide-react"
import { cn } from "@/components/utils"

export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center justify-center min-h-[120px]", className)}>
      <Loader2 className="h-8 w-8 animate-spin text-zinc-400" aria-hidden />
    </div>
  )
}
