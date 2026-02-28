"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, CheckCircle2, XCircle, Loader2, FileText, Database, Sparkles, AlertTriangle, Ruler } from "lucide-react"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import { cn } from "@/components/utils"

type AipSummary = {
  id: string
  name: string
  status: string
  obstaclesCount: number
  runwaysCount: number
}

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
  aips?: AipSummary[]
}

function nameFromUrl(url: string): string {
  try {
    const path = new URL(url).pathname
    const m = path.match(/\/([A-Z0-9]{4})\.pdf/i) || path.match(/\/([A-Z0-9]+)/i)
    return m ? m[1].toUpperCase() : "PDF"
  } catch {
    return "PDF"
  }
}

type StepPhase = "idle" | "mineru" | "saving"

export default function JobDetailPage() {
  const params = useParams()
  const jobId = params.jobId as string
  const [job, setJob] = useState<JobState | null>(null)
  const [loading, setLoading] = useState(true)
  const [stepPhase, setStepPhase] = useState<StepPhase>("idle")
  const steppingRef = useRef(false)

  const fetchJob = useCallback(
    () =>
      fetch(`/api/jobs/${jobId}`)
        .then((r) => r.json())
        .then((data) => {
          if (data.id) setJob(data)
        }),
    [jobId]
  )

  useEffect(() => {
    fetchJob().finally(() => setLoading(false))
  }, [fetchJob])

  useEffect(() => {
    if (!job || job.status !== "pending") {
      setStepPhase("idle")
      return
    }
    if (steppingRef.current) return
    if (job.processedCount >= job.count) return

    steppingRef.current = true
    setStepPhase("mineru")
    fetch(`/api/jobs/${jobId}/step`, { method: "POST" })
      .then((r) => r.json())
      .then(() => {
        setStepPhase("saving")
        setTimeout(() => {
          fetchJob().then(() => {
            setStepPhase("idle")
          })
        }, 500)
      })
      .catch(() => setStepPhase("idle"))
      .finally(() => {
        steppingRef.current = false
      })
  }, [job?.status, job?.processedCount, job?.count, jobId, fetchJob])

  useEffect(() => {
    if (!job || job.status !== "pending") return
    const t = setInterval(fetchJob, 4000)
    return () => clearInterval(t)
  }, [jobId, job?.status, fetchJob])

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
  const currentIndex = job.processedCount
  const currentFileUrl = job.urls[currentIndex]
  const currentFileName = currentFileUrl ? nameFromUrl(currentFileUrl) : "—"
  const currentStepLabel =
    stepPhase === "mineru"
      ? "Extracting with MinerU..."
      : stepPhase === "saving"
        ? "Saving to database..."
        : null

  const stepStates: ("done" | "active" | "upcoming")[] =
    stepPhase === "mineru"
      ? ["done", "active", "upcoming"]
      : stepPhase === "saving"
        ? ["done", "done", "active"]
        : ["active", "upcoming", "upcoming"]

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

      {isPending && currentIndex < job.count && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-4 mb-6 space-y-3">
          <p className="text-sm font-medium text-white flex items-center gap-2">
            <FileText className="h-4 w-4 text-zinc-400" />
            Processing file {currentIndex + 1} of {job.count}: <span className="font-mono text-white">{currentFileName}</span>
          </p>
          <ol className="space-y-1.5 text-sm">
            <li
              className={cn(
                "flex items-center gap-2",
                stepStates[0] === "done"
                  ? "text-zinc-500 opacity-70"
                  : stepStates[0] === "active"
                    ? "text-zinc-200"
                    : "text-zinc-300"
              )}
            >
              {stepStates[0] === "done" ? (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
              ) : (
                <span className="w-4 shrink-0 text-zinc-500">1.</span>
              )}
              Processing this file ({currentFileName})
            </li>
            <li
              className={cn(
                "flex items-center gap-2",
                stepStates[1] === "done"
                  ? "text-zinc-500 opacity-70"
                  : stepStates[1] === "active"
                    ? "text-zinc-200"
                    : "text-zinc-300"
              )}
            >
              {stepStates[1] === "done" ? (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
              ) : stepStates[1] === "active" ? (
                <Loader2 className="h-4 w-4 shrink-0 animate-spin text-zinc-400" />
              ) : (
                <span className="w-4 shrink-0 text-zinc-500">2.</span>
              )}
              Extracting data with MinerU
            </li>
            <li
              className={cn(
                "flex items-center gap-2",
                stepStates[2] === "done"
                  ? "text-zinc-500 opacity-70"
                  : stepStates[2] === "active"
                    ? "text-zinc-200"
                    : "text-zinc-300"
              )}
            >
              {stepStates[2] === "active" ? (
                <Loader2 className="h-4 w-4 shrink-0 animate-spin text-zinc-400" />
              ) : stepStates[2] === "done" ? (
                <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
              ) : (
                <span className="w-4 shrink-0 text-zinc-500">3.</span>
              )}
              Saving to database
            </li>
          </ol>
          {currentStepLabel && (
            <p className="text-xs text-zinc-500 pt-1">
              {stepPhase === "mineru" && <Sparkles className="h-3 w-3 inline mr-1" />}
              {stepPhase === "saving" && <Database className="h-3 w-3 inline mr-1" />}
              {currentStepLabel}
            </p>
          )}
        </div>
      )}

      {job.status === "success" && (
        <div className="space-y-4">
          {job.aips && job.aips.length > 0 && (
            <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
              <p className="text-sm font-medium text-white mb-3">Parsed AIPs · obstacles & runways</p>
              <ul className="space-y-2">
                {job.aips.map((aip) => (
                  <li key={aip.id} className="flex items-center gap-3 text-sm">
                    <span className="font-mono text-white w-12">{aip.name}</span>
                    <span className="text-zinc-400 flex items-center gap-1.5">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      {aip.obstaclesCount} obstacles
                    </span>
                    <span className="text-zinc-400 flex items-center gap-1.5">
                      <Ruler className="h-3.5 w-3.5" />
                      {aip.runwaysCount} runways
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <Link
            href={`/aips?jobId=${job.id}`}
            className="inline-flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-white hover:bg-zinc-700"
          >
            View parsed AIPs from this job
          </Link>
        </div>
      )}
    </div>
  )
}
