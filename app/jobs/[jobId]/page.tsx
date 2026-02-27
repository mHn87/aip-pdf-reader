"use client"

import { useEffect, useState, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, CheckCircle2, XCircle, Clock, Loader2 } from "lucide-react"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { cn } from "@/components/utils"

type JobState = {
  id: string
  count: number
  status: string
  processedCount: number
  createdAt: string
  completedAt: string | null
  durationMs: number | null
  errorMessage: string | null
  urls: string[]
}

export default function JobDetailPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.jobId as string
  const [job, setJob] = useState<JobState | null>(null)
  const [loading, setLoading] = useState(true)
  const steppingRef = useRef(false)

  const fetchJob = () =>
    fetch(`/api/jobs/${jobId}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.id) setJob(data)
      })

  useEffect(() => {
    fetchJob().finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId])

  useEffect(() => {
    if (!job || job.status !== "pending") return
    if (steppingRef.current) return
    if (job.processedCount >= job.count) return

    steppingRef.current = true
    fetch(`/api/jobs/${jobId}/step`, { method: "POST" })
      .then((r) => r.json())
      .then(() => fetchJob())
      .finally(() => {
        steppingRef.current = false
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job?.status, job?.processedCount, job?.count, jobId])

  useEffect(() => {
    if (!job || job.status !== "pending") return
    const t = setInterval(fetchJob, 4000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, job?.status])

  if (loading || !job) {
    return (
      <div className="container px-4 py-6 md:py-8">
        <Link href="/jobs" className="text-zinc-400 hover:text-white mb-4 inline-flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Jobs
        </Link>
        {loading ? <LoadingSpinner className="min-h-[30vh]" /> : <p className="text-zinc-500 text-center py-8">Job not found.</p>}
      </div>
    )
  }

  const isPending = job.status === "pending"
  const progress = `${job.processedCount}/${job.count}`

  return (
    <div className="container max-w-screen-xl mx-auto px-4 py-6 md:py-8">
      <Link href="/jobs" className="text-zinc-400 hover:text-white mb-6 inline-flex items-center gap-1">
        <ArrowLeft className="h-4 w-4" /> Jobs
      </Link>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0">
          <span className="font-mono text-sm sm:text-lg text-white truncate">{job.id}</span>
          {isPending && (
            <span className="text-sm text-zinc-500" title={progress}>
              {progress}
            </span>
          )}
        </div>
        <span
          className={cn(
            "inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium",
            job.status === "success" && "bg-green-500/20 text-green-400",
            job.status === "error" && "bg-red-500/20 text-red-400",
            job.status === "pending" && "bg-amber-500/20 text-amber-400"
          )}
        >
          {job.status === "success" && <CheckCircle2 className="h-4 w-4" />}
          {job.status === "error" && <XCircle className="h-4 w-4" />}
          {job.status === "pending" && <Loader2 className="h-4 w-4 animate-spin" />}
          {job.status}
        </span>
      </div>
      {job.durationMs != null && job.completedAt && (
        <p className="text-zinc-500 text-sm mb-4">Duration: {Math.round(job.durationMs / 1000)}s</p>
      )}
      {job.status === "error" && job.errorMessage && (
        <p className="text-red-400 text-sm mb-4">{job.errorMessage}</p>
      )}
      {job.status === "success" && (
        <Link
          href={`/aips?jobId=${job.id}`}
          className="inline-flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-white hover:bg-zinc-700"
        >
          View parsed AIPs from this job
        </Link>
      )}
    </div>
  )
}
