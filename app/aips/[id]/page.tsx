"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { ArrowLeft, AlertTriangle, Ruler } from "lucide-react"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

const tableStyle = `
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #686868; padding: 4px 8px; text-align: left; }
`

type AipData = {
  id: string
  name: string
  status: string
  sourceUrl?: string
  runways: Record<string, { parse: string; extract: unknown }> | null
  obstacles: Record<string, { parse: string; extract: unknown }> | null
}

export default function AipViewPage() {
  const params = useParams()
  const id = params.id as string
  const [aip, setAip] = useState<AipData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/aips/${id}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.id) setAip(data)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading || !aip) {
    return (
      <div className="container px-4 py-6 md:py-8">
        {loading ? <LoadingSpinner className="min-h-[40vh]" /> : <p className="text-zinc-500 text-center py-12">AIP not found.</p>}
      </div>
    )
  }

  const obstaclesEntries = aip.obstacles ? Object.entries(aip.obstacles) : []
  const runwaysEntries = aip.runways ? Object.entries(aip.runways) : []

  return (
    <div className="container max-w-screen-xl mx-auto px-4 py-6 md:py-8">
      <Link
        href="/aips"
        className="text-zinc-400 hover:text-white mb-6 inline-flex items-center gap-1"
      >
        <ArrowLeft className="h-4 w-4" /> Parsed AIPs
      </Link>
      <h1 className="text-xl md:text-2xl font-bold text-white mb-2">{aip.name}</h1>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mb-8">
        <p className="text-zinc-500 text-sm">Read-only view (from database)</p>
        {aip.sourceUrl && (
          <a
            href={aip.sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 underline-offset-2 hover:underline"
          >
            Open original PDF
          </a>
        )}
      </div>

      <div className="grid gap-6">
        {obstaclesEntries.length > 0 && (
          <Card className="bg-zinc-950 border-zinc-800">
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-zinc-400" />
                <CardTitle className="text-lg text-white">AD 2.10 - Obstacles</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {obstaclesEntries.map(([key, val]) => (
                <div
                  key={key}
                  dangerouslySetInnerHTML={{
                    __html: `<style>${tableStyle}</style>${val.parse}`,
                  }}
                />
              ))}
            </CardContent>
          </Card>
        )}
        {runwaysEntries.length > 0 && (
          <Card className="bg-zinc-950 border-zinc-800">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Ruler className="h-5 w-5 text-zinc-400" />
                <CardTitle className="text-lg text-white">AD 2.12 - Runway Characteristics</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {runwaysEntries.map(([key, val]) => (
                <div
                  key={key}
                  dangerouslySetInnerHTML={{
                    __html: `<style>${tableStyle}</style>${val.parse}`,
                  }}
                />
              ))}
            </CardContent>
          </Card>
        )}
        {obstaclesEntries.length === 0 && runwaysEntries.length === 0 && (
          <p className="text-zinc-500">No obstacles or runways data.</p>
        )}
      </div>
    </div>
  )
}
