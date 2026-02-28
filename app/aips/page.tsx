"use client"

import { useEffect, useState, Suspense } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { cn } from "@/components/utils"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { Trash2, Loader2 } from "lucide-react"

type AipItem = {
  id: string
  name: string
  status: string
  createdAt: string
  jobId: string
  obstaclesCount: number
  runwaysCount: number
}

function AipsContent() {
  const searchParams = useSearchParams()
  const jobId = searchParams.get("jobId")
  const [aips, setAips] = useState<AipItem[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    setLoading(true)
    const url = jobId ? `/api/aips?jobId=${encodeURIComponent(jobId)}` : "/api/aips"
    fetch(url)
      .then((r) => r.json())
      .then((data) => {
        if (data.aips) setAips(data.aips)
      })
      .finally(() => setLoading(false))
  }, [jobId])

  const handleDeleteAll = async () => {
    if (!confirm("Delete all parsed AIPs?")) return
    setDeleting(true)
    try {
      const res = await fetch("/api/aips", { method: "DELETE" })
      const data = await res.json()
      if (data.success) setAips([])
      else alert(data.error || "Failed")
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return <LoadingSpinner className="min-h-[50vh]" />
  }

  return (
    <div className="container max-w-screen-xl mx-auto px-4 py-6 md:py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-white mb-1">Parsed AIPs</h1>
          {jobId && (
            <p className="text-zinc-500 text-sm">Filtered by job: {jobId}</p>
          )}
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleDeleteAll}
          disabled={deleting || aips.length === 0}
          className="gap-2 border-zinc-700 text-zinc-300 hover:bg-red-500/10 hover:border-red-500/50 hover:text-red-400 w-fit"
        >
          {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          Delete all
        </Button>
      </div>

      {aips.length === 0 ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <p className="text-zinc-500">No AIPs found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 md:gap-4">
          {aips.map((aip) => {
            const card = (
              <>
                <div className="font-semibold text-white truncate">{aip.name}</div>
                <div className="text-xs text-zinc-500 mt-1">
                  {new Date(aip.createdAt).toLocaleDateString("en-GB", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                </div>
                <div className="text-xs text-zinc-500 mt-0.5">
                  {aip.obstaclesCount} obstacles · {aip.runwaysCount} runways
                </div>
              </>
            )
            const className = cn(
              "rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 md:p-4 transition-colors",
              aip.status === "pending" && "opacity-60",
              aip.status === "success" && "hover:bg-zinc-800/50"
            )
            return aip.status === "success" ? (
              <Link key={aip.id} href={`/aips/${aip.id}`} className={className}>
                {card}
              </Link>
            ) : (
              <div key={aip.id} className={className}>
                {card}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function AipsPage() {
  return (
    <Suspense fallback={<LoadingSpinner className="min-h-[50vh]" />}>
      <AipsContent />
    </Suspense>
  )
}
