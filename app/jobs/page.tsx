"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Layers, CheckCircle2, XCircle, Clock, Trash2, Loader2 } from "lucide-react"
import { cn } from "@/components/utils"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

type Job = {
  id: string
  count: number
  status: string
  processedCount: number
  createdAt: string
  completedAt: string | null
  durationMs: number | null
  errorMessage: string | null
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)

  const fetchJobs = () =>
    fetch("/api/jobs")
      .then((r) => r.json())
      .then((data) => {
        if (data.jobs) setJobs(data.jobs)
      })

  useEffect(() => {
    fetchJobs().finally(() => setLoading(false))
  }, [])

  const handleDeleteAll = async () => {
    if (!confirm("Delete all jobs (and their AIPs)?")) return
    setDeleting(true)
    try {
      const res = await fetch("/api/jobs", { method: "DELETE" })
      const data = await res.json()
      if (data.success) setJobs([])
      else alert(data.error || "Failed")
    } finally {
      setDeleting(false)
    }
  }

  if (loading) return <LoadingSpinner className="min-h-[40vh]" />

  return (
    <div className="container max-w-screen-xl mx-auto px-4 py-6 md:py-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-6">
        <h1 className="text-xl md:text-2xl font-bold text-white">Jobs</h1>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleDeleteAll}
          disabled={deleting || jobs.length === 0}
          className="gap-2 border-zinc-700 text-zinc-300 hover:bg-red-500/10 hover:border-red-500/50 hover:text-red-400 w-fit"
        >
          {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          Delete all
        </Button>
      </div>
      <div className="space-y-2">
        {jobs.length === 0 && (
          <p className="text-zinc-500 text-center py-8">No jobs yet. Create one from Batch parse.</p>
        )}
        {jobs.map((job) => (
          <Link
            key={job.id}
            href={`/jobs/${job.id}`}
            className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-3 sm:px-4 hover:bg-zinc-800/50 transition-colors"
          >
            <div className="flex items-center gap-2 sm:gap-3 min-w-0">
              <span className="font-mono text-xs sm:text-sm text-white truncate">{job.id}</span>
              <span
                className="text-xs text-zinc-500 shrink-0"
                title={job.status === "pending" ? `${job.processedCount}/${job.count}` : undefined}
              >
                {job.status === "pending" ? `${job.processedCount}/${job.count}` : `${job.count} URLs`}
              </span>
            </div>
            <div className="flex items-center gap-2 sm:gap-3">
              {job.durationMs != null && job.completedAt && (
                <span className="text-xs text-zinc-500">{Math.round(job.durationMs / 1000)}s</span>
              )}
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium",
                  job.status === "success" && "bg-green-500/20 text-green-400",
                  job.status === "error" && "bg-red-500/20 text-red-400",
                  job.status === "pending" && "bg-amber-500/20 text-amber-400"
                )}
              >
                {job.status === "success" && <CheckCircle2 className="h-3 w-3" />}
                {job.status === "error" && <XCircle className="h-3 w-3" />}
                {job.status === "pending" && <Clock className="h-3 w-3" />}
                {job.status}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
