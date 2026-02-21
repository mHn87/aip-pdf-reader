import { useState, useEffect } from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertCircle, CheckCircle2, AlertTriangle, Ruler } from "lucide-react"
import './styles.css'

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

export function DataTables({ enabled }: { enabled: boolean }) {
  const [tables, setTables] = useState<TablesResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    if (!enabled) {
      setTables(null)
      setError(null)
      return
    }
    
    const fileData = typeof window !== "undefined" ? localStorage.getItem("aip_fileData") : null
    if (!fileData) {
      setError("No PDF in storage.")
      return
    }
    
    setLoading(true)
    setError(null)
    fetch("/api/elements", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fileData }),
    })
      .then((r) => r.json())
      .then((result) => {
        if (result.success && result.tables) {
          setTables(result.tables)
        } else {
          setError(result.error || "Failed to load tables")
        }
      })
      .catch(() => setError("Failed to load tables"))
      .finally(() => setLoading(false))
  }, [enabled])
  
  if (!enabled) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
        <AlertCircle className="h-12 w-12 mb-4 opacity-50" />
        <p>Upload a PDF to view tables</p>
      </div>
    )
  }
  
  if (loading) {
    return (
      <div className="grid gap-6">
        <Card className="bg-zinc-950 border-zinc-800 p-8">
          <p className="text-muted-foreground mb-4">Loading PDF tables…</p>
          <TableSkeleton />
        </Card>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="text-red-400 flex items-center gap-2">
        <AlertCircle className="h-5 w-5" />
        <p>{error}</p>
      </div>
    )
  }
  
  if (!tables) return null
  
  return (
    <div className="grid gap-6">
      {/* AD 2.10 */}
      {tables.AD_2_10 && tables.AD_2_10.length > 0 && (
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-zinc-800 text-white">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-lg text-white">AD 2.10 - Obstacles</CardTitle>
                <CardDescription className="text-zinc-400">Click each runway to see obstacles</CardDescription>
              </div>
              <CheckCircle2 className="h-5 w-5 text-green-500 ml-auto" />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {tables.AD_2_10.map((html, idx) => (
              <div
                key={idx}
                dangerouslySetInnerHTML={{
                  __html: `
      <style>
table {
  border-collapse: collapse; /* مهم برای اینکه خطوط تداخل نکنند */
  width: 100%;
}

th, td {
  border: 1px solid #686868; /* خط خاکستری دور هر سلول */
  padding: 4px 8px;        /* کمی فاصله داخل سلول */
  text-align: left;
}      </style>
      ${html}
    `
                }}              />
            ))}
          </CardContent>
        </Card>
      )}
      
      {/* AD 2.12 */}
      {tables.AD_2_12 && tables.AD_2_12.length > 0 && (
        <Card className="bg-zinc-950 border-zinc-800">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-zinc-800 text-white">
                <Ruler className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-lg text-white">AD 2.12 - Runway Characteristics</CardTitle>
                <CardDescription className="text-zinc-400">Click each runway to see details</CardDescription>
              </div>
              <CheckCircle2 className="h-5 w-5 text-green-500 ml-auto" />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {tables.AD_2_12.map((html, idx) => (
              <div
                key={idx}
                dangerouslySetInnerHTML={{
                  __html: `
      <style>
table {
  border-collapse: collapse; /* مهم برای اینکه خطوط تداخل نکنند */
  width: 100%;
}

th, td {
  border: 1px solid #686868; /* خط خاکستری دور هر سلول */
  padding: 4px 8px;        /* کمی فاصله داخل سلول */
  text-align: left;
}      </style>
      ${html}
    `
                }}              />
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}