"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ListPlus, Loader2, AlertCircle } from "lucide-react"

export default function BatchParsePage() {
  const router = useRouter()
  const [text, setText] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async () => {
    const urls = text
      .split(/[\n,]/)
      .map((u) => u.trim())
      .filter(Boolean)
    if (urls.length === 0) {
      setError("Enter at least one PDF URL (one per line or comma-separated).")
      return
    }
    setError(null)
    setLoading(true)
    try {
      const res = await fetch("/api/jobs/validate-and-create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || "Validation failed")
        return
      }
      router.push(`/jobs/${data.jobId}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container max-w-screen-xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-xl md:text-2xl font-bold text-white mb-2">Batch parse</h1>
      <p className="text-zinc-400 mb-6">
        Add PDF URLs (one per line or comma-separated). All must be valid PDFs; then a job is created and you are redirected to Jobs.
      </p>
      <div className="space-y-4">
        <textarea
          placeholder={"https://example.com/1.pdf\nhttps://example.com/2.pdf"}
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={10}
          className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-white placeholder-zinc-500 focus:border-zinc-500 focus:outline-none resize-y"
        />
        {error && (
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <p>{error}</p>
          </div>
        )}
        <Button onClick={submit} disabled={loading} className="gap-2">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ListPlus className="h-4 w-4" />}
          Validate & create job
        </Button>
      </div>
    </div>
  )
}
