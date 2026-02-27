"use client"

import { useState, useCallback } from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { AlertCircle, CheckCircle2, AlertTriangle, Ruler } from "lucide-react"
import { LoadingSpinner } from "@/components/ui/loading-spinner"
import "./styles.css"

type TablesResponse = {
  AD_2_10?: string[]
  AD_2_12?: string[]
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: 2 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

const tableStyle = `
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #686868; padding: 4px 8px; text-align: left; }
`

export function DataTables({ url }: { url: string }) {
  const [tables, setTables] = useState<TablesResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runParse = useCallback(() => {
    if (!url?.trim()) return
    setLoading(true)
    setError(null)
    setTables(null)
    fetch("/api/pdf-to-elements", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pdfUrl: url.trim() }),
    })
      .then((r) => r.json())
      .then((result) => {
        if (result.success && result.tables) setTables(result.tables)
        else setError(result.error || "Failed to load tables")
      })
      .catch(() => setError("Failed to load tables"))
      .finally(() => setLoading(false))
  }, [url])

  if (!url) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-zinc-400">
        <AlertCircle className="h-12 w-12 mb-4 opacity-50" />
        <p>Enter a PDF URL above and click Parse</p>
      </div>
    )
  }

  if (!tables && !loading && !error) {
    return (
      <Card className="bg-zinc-950 border-zinc-800 p-8">
        <p className="text-zinc-400 mb-4">URL entered. Click Parse to run MinerU.</p>
        <Button type="button" onClick={runParse}>Parse (MinerU)</Button>
      </Card>
    )
  }

  if (loading) {
    return (
      <Card className="bg-zinc-950 border-zinc-800 p-8">
        <LoadingSpinner className="mb-4" />
        <TableSkeleton />
      </Card>
    )
  }

  if (error) {
    return (
      <div className="space-y-3">
        <div className="text-red-400 flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          <p>{error}</p>
        </div>
        <Button type="button" variant="outline" onClick={runParse}>Try again</Button>
      </div>
    )
  }

  if (!tables) return null

  return (
    <div className="grid gap-6">
      {tables.AD_2_10 && tables.AD_2_10.length > 0 && (
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-zinc-800 text-white">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-lg text-white">AD 2.10 - Obstacles</CardTitle>
                <CardDescription className="text-zinc-400">Obstacles table(s)</CardDescription>
              </div>
              <CheckCircle2 className="h-5 w-5 text-green-500 ml-auto" />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {tables.AD_2_10.map((html, idx) => (
              <div key={idx} dangerouslySetInnerHTML={{ __html: `<style>${tableStyle}</style>${html}` }} />
            ))}
          </CardContent>
        </Card>
      )}
      {(!tables.AD_2_10 || tables.AD_2_10.length === 0) && (
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader>
            <CardTitle className="text-lg text-white">AD 2.10 - Obstacles</CardTitle>
            <CardDescription className="text-zinc-400">No AD 2.10 table detected</CardDescription>
          </CardHeader>
        </Card>
      )}
      {tables.AD_2_12 && tables.AD_2_12.length > 0 && (
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-zinc-800 text-white">
                <Ruler className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-lg text-white">AD 2.12 - Runway Characteristics</CardTitle>
                <CardDescription className="text-zinc-400">Runway table(s)</CardDescription>
              </div>
              <CheckCircle2 className="h-5 w-5 text-green-500 ml-auto" />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {tables.AD_2_12.map((html, idx) => (
              <div key={idx} dangerouslySetInnerHTML={{ __html: `<style>${tableStyle}</style>${html}` }} />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
