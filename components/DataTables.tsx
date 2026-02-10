import { useState, useEffect, useRef } from "react"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { AlertCircle, CheckCircle2, MapPin, AlertTriangle, Ruler, Navigation, ChevronDown, ChevronRight } from "lucide-react"

// هر element از Unstructured (برای تایپ بدنه درخواست)
type ElementItem = Record<string, unknown>

interface DataTableProps {
  endpoint: string
  title: string
  description: string
  icon: React.ReactNode
  enabled: boolean
  fileId?: string | null
  /** وقتی از /api/elements گرفته شده؛ پارس فقط برای همین بخش و فقط وقتی کارت در viewport است */
  elements?: ElementItem[] | null
  elementsLoading?: boolean
}

function TableSkeleton() {
  return (
    <div className="space-y-3">
      <Skeleton className="h-10 w-full" />
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-12 w-full" />
      ))}
    </div>
  )
}

// Expandable Row Component
function ExpandableRow({ title, count, children }: { title: string; count?: number; children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  
  return (
    <div className="border border-border rounded-lg mb-2 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-4 py-3 bg-zinc-900 hover:bg-zinc-800 transition-colors text-left"
      >
        {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        <span className="font-medium text-white">{title}</span>
        {count !== undefined && (
          <span className="text-zinc-400 text-sm ml-2">({count} items)</span>
        )}
      </button>
      {open && <div className="p-3 bg-zinc-950">{children}</div>}
    </div>
  )
}

function DataTable({ endpoint, title, description, icon, enabled, fileId, elements, elementsLoading }: DataTableProps) {
  const [data, setData] = useState<unknown>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const cardRef = useRef<HTMLDivElement>(null)
  const hasFetchedForView = useRef(false)

  // فقط وقتی این کارت در viewport است با elements همان بخش را پارس می‌کنیم (یک بار Unstructured، دونه‌دونه پارس)
  useEffect(() => {
    if (!enabled || !elements || elements.length === 0 || elementsLoading) {
      if (!enabled) {
        setData(null)
        setError(null)
        hasFetchedForView.current = false
      }
      return
    }

    const el = cardRef.current
    if (!el) return

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries
        if (!entry.isIntersecting || hasFetchedForView.current) return
        hasFetchedForView.current = true
        setLoading(true)
        setError(null)
        fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ elements }),
        })
          .then((r) => r.json())
          .then((result) => {
            if (result.success) setData(result.data)
            else setError(result.error || "Failed to parse data")
          })
          .catch(() => setError("Failed to fetch data"))
          .finally(() => setLoading(false))
      },
      { rootMargin: "80px", threshold: 0.1 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [enabled, endpoint, elements, elementsLoading])

  // اگر elements نداشتیم (fallback قدیمی) با fileData همه را یک‌جا می‌خوانیم
  useEffect(() => {
    if (!enabled || (elements !== undefined && elements !== null)) return
    const fileData = typeof window !== "undefined" ? localStorage.getItem("aip_fileData") : null
    if (!fileData) {
      setError("No PDF uploaded. Please upload a PDF first.")
      return
    }
    setLoading(true)
    setError(null)
    fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fileData }),
    })
      .then((r) => r.json())
      .then((result) => {
        if (result.success) setData(result.data)
        else setError(result.error || "Failed to parse data")
      })
      .catch(() => setError("Failed to fetch data"))
      .finally(() => setLoading(false))
  }, [enabled, endpoint, elements])

  const renderContent = () => {
    if (!enabled) {
      return (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <AlertCircle className="h-12 w-12 mb-4 opacity-50" />
          <p>Upload a PDF to view data</p>
        </div>
      )
    }

    if (loading) {
      return <TableSkeleton />
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center py-12 text-red-400">
          <AlertCircle className="h-12 w-12 mb-4" />
          <p>{error}</p>
        </div>
      )
    }

    if (showPlaceholder) {
      return (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <p className="text-sm">Scroll into view to parse this section</p>
        </div>
      )
    }
    if (!data) {
      return (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <p>No data available</p>
        </div>
      )
    }

    // Render based on endpoint - ORDER MATTERS! Check longer strings first
    if (endpoint.includes('ad2_10')) {
      return <AD210Table data={data as Record<string, Array<{ Coordinates: string; "Obstacle type Elevation/HGT Markings/LGT": string }>>} />
    }
    if (endpoint.includes('ad2_12')) {
      return <AD212Table data={data as Array<Record<string, string | null>>} />
    }
    if (endpoint.includes('ad2_13')) {
      return <AD213Table data={data as Array<{ "RWY Designator"?: string; RWY_Designator?: string; entries: Array<Record<string, string | null>> }> } />
    }
    if (endpoint.includes('ad2_1')) {
      return <AD21Table data={data as Record<string, string>} />
    }
    if (endpoint.includes('ad2_2')) {
      return <AD22Table data={data as Array<{ field: string; value: string }>} />
    }

    return <pre className="text-xs overflow-auto p-4 bg-zinc-900 rounded">{JSON.stringify(data, null, 2)}</pre>
  }

  const showPlaceholder = enabled && elements && elements.length > 0 && !elementsLoading && !loading && !error && data === null
  return (
    <div ref={cardRef}>
    <Card className="bg-zinc-950 border-zinc-800">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-zinc-800 text-white">
            {icon}
          </div>
          <div>
            <CardTitle className="text-lg text-white">{title}</CardTitle>
            <CardDescription className="text-zinc-400">{description}</CardDescription>
          </div>
          {enabled && !loading && !error && data !== null && (
            <CheckCircle2 className="h-5 w-5 text-green-500 ml-auto" />
          )}
        </div>
      </CardHeader>
      <CardContent>
        {renderContent()}
      </CardContent>
    </Card>
    </div>
  )
}

// AD 2.1 - Simple key-value
function AD21Table({ data }: { data: Record<string, string> }) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="border-zinc-800">
          <TableHead className="text-zinc-400">Field</TableHead>
          <TableHead className="text-zinc-400">Value</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow className="border-zinc-800">
          <TableCell className="text-zinc-300">ICAO Code</TableCell>
          <TableCell className="font-mono text-green-400 text-lg">{data.name || '-'}</TableCell>
        </TableRow>
        <TableRow className="border-zinc-800">
          <TableCell className="text-zinc-300">City</TableCell>
          <TableCell className="text-white">{data.country || '-'}</TableCell>
        </TableRow>
        <TableRow className="border-zinc-800">
          <TableCell className="text-zinc-300">Airport Name</TableCell>
          <TableCell className="text-white">{data.aip || data.fullname || '-'}</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  )
}

// AD 2.2 - Simple key-value array
function AD22Table({ data }: { data: Array<{ field: string; value: string }> }) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="border-zinc-800">
          <TableHead className="text-zinc-400 w-1/3">Field</TableHead>
          <TableHead className="text-zinc-400">Value</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((item, idx) => (
          <TableRow key={idx} className="border-zinc-800">
            <TableCell className="text-zinc-300">{item.field}</TableCell>
            <TableCell className="font-mono text-white text-sm">{item.value || '-'}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

// AD 2.10 - NESTED: RWY -> Obstacles
function AD210Table({ data }: { data: Record<string, Array<{ Coordinates: string; "Obstacle type Elevation/HGT Markings/LGT": string }>> }) {
  const entries = Object.entries(data)
  
  return (
    <div className="space-y-2">
      <p className="text-sm text-zinc-400 mb-4">
        {entries.length} runway areas • {entries.reduce((a, [, v]) => a + v.length, 0)} total obstacles
      </p>
      
      {entries.map(([rwy, obstacles]) => (
        <ExpandableRow key={rwy} title={rwy} count={obstacles.length}>
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800">
                <TableHead className="text-zinc-400 w-12">#</TableHead>
                <TableHead className="text-zinc-400">Coordinates</TableHead>
                <TableHead className="text-zinc-400">Obstacle Info</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {obstacles.map((obs, idx) => (
                <TableRow key={idx} className="border-zinc-800">
                  <TableCell className="text-zinc-500">{idx + 1}</TableCell>
                  <TableCell className="font-mono text-blue-400 text-sm">{obs.Coordinates || '-'}</TableCell>
                  <TableCell className="text-white text-sm">{obs["Obstacle type Elevation/HGT Markings/LGT"] || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ExpandableRow>
      ))}
    </div>
  )
}

// AD 2.12 - NESTED: Each runway is expandable
function AD212Table({ data }: { data: Array<Record<string, string | null>> }) {
  // Get all keys except _unit fields
  const allKeys = Array.from(new Set(data.flatMap(obj => Object.keys(obj)))).filter(k => !k.endsWith('_unit'))
  
  return (
    <div className="space-y-2">
      <p className="text-sm text-zinc-400 mb-4">{data.length} runways</p>
      
      {data.map((runway, idx) => {
        const rwyName = runway["Designations RWY NR"] || `Runway ${idx + 1}`
        
        return (
          <ExpandableRow key={idx} title={`Runway ${rwyName}`}>
            <Table>
              <TableHeader>
                <TableRow className="border-zinc-800">
                  <TableHead className="text-zinc-400 w-1/2">Property</TableHead>
                  <TableHead className="text-zinc-400">Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {allKeys.map((key) => {
                  const value = runway[key]
                  const unit = runway[`${key}_unit`]
                  
                  return (
                    <TableRow key={key} className="border-zinc-800">
                      <TableCell className="text-zinc-300 text-sm">{key}</TableCell>
                      <TableCell className="font-mono text-white text-sm">
                        {value !== null ? (
                          <>
                            {value}
                            {unit && <span className="text-zinc-500 ml-1">({unit})</span>}
                          </>
                        ) : (
                          <span className="text-zinc-600 italic">null</span>
                        )}
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </ExpandableRow>
        )
      })}
    </div>
  )
}

// AD 2.13 - NESTED: Runway -> Entries
function AD213Table({ data }: { data: Array<{ "RWY Designator"?: string; RWY_Designator?: string; entries: Array<Record<string, string | null>> }> }) {
  const totalEntries = data.reduce((acc, rwy) => acc + (rwy.entries?.length || 0), 0)
    
  return (
    <div className="space-y-2">
      <p className="text-sm text-zinc-400 mb-4">{data.length} runways • {totalEntries} distance declarations</p>
      
      {data.map((runway, idx) => {
        const rwyName = runway["RWY Designator"] || runway.RWY_Designator || `Runway ${idx + 1}`
        const entries = runway.entries || []
        
        return (
          <ExpandableRow key={idx} title={`Runway ${rwyName}`} count={entries.length}>
            <Table>
              <TableHeader>
                <TableRow className="border-zinc-800">
                  <TableHead className="text-zinc-400 w-10">#</TableHead>
                  <TableHead className="text-zinc-400">TORA</TableHead>
                  <TableHead className="text-zinc-400">TODA</TableHead>
                  <TableHead className="text-zinc-400">ASDA</TableHead>
                  <TableHead className="text-zinc-400">LDA</TableHead>
                  <TableHead className="text-zinc-400">Remarks</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry, i) => (
                  <TableRow key={i} className="border-zinc-800">
                    <TableCell className="text-zinc-500">{i + 1}</TableCell>
                    <TableCell className="font-mono text-white">
                      {entry.TORA || '-'} <span className="text-zinc-500 text-xs">{entry.TORA_unit || 'M'}</span>
                    </TableCell>
                    <TableCell className="font-mono text-white">
                      {entry.TODA || '-'} <span className="text-zinc-500 text-xs">{entry.TODA_unit || 'M'}</span>
                    </TableCell>
                    <TableCell className="font-mono text-white">
                      {entry.ASDA || '-'} <span className="text-zinc-500 text-xs">{entry.ASDA_unit || 'M'}</span>
                    </TableCell>
                    <TableCell className="font-mono text-white">
                      {entry.LDA || '-'} <span className="text-zinc-500 text-xs">{entry.LDA_unit || 'M'}</span>
                    </TableCell>
                    <TableCell className="text-zinc-300 text-sm">{entry.Remarks || '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ExpandableRow>
        )
      })}
    </div>
  )
}

export function DataTables({ enabled, fileId }: { enabled: boolean; fileId?: string | null }) {
  const [elements, setElements] = useState<ElementItem[] | null>(null)
  const [elementsLoading, setElementsLoading] = useState(false)
  const [elementsError, setElementsError] = useState<string | null>(null)

  // یک بار به Unstructured می‌زنیم؛ بعد دونه‌دونه فقط وقتی viewport روی هر بخش است همان را پارس می‌کنیم
  useEffect(() => {
    if (!enabled) {
      setElements(null)
      setElementsError(null)
      return
    }
    const fileData = typeof window !== "undefined" ? localStorage.getItem("aip_fileData") : null
    if (!fileData) {
      setElementsError("No PDF in storage.")
      return
    }
    setElementsLoading(true)
    setElementsError(null)
    fetch("/api/elements", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fileData }),
    })
      .then((r) => r.json())
      .then((result) => {
        if (result.success && Array.isArray(result.elements)) setElements(result.elements)
        else setElementsError(result.error || "Failed to load elements")
      })
      .catch(() => setElementsError("Failed to load elements"))
      .finally(() => setElementsLoading(false))
  }, [enabled, fileId])

  const tables = [
    { endpoint: "/api/parse/ad2_1", title: "AD 2.1 - Location Indicator", description: "Aerodrome location indicator and name", icon: <MapPin className="h-5 w-5" /> },
    { endpoint: "/api/parse/ad2_2", title: "AD 2.2 - Geographical Data", description: "Aerodrome geographical and administrative data", icon: <MapPin className="h-5 w-5" /> },
    { endpoint: "/api/parse/ad2_10", title: "AD 2.10 - Obstacles", description: "Click each runway to see obstacles", icon: <AlertTriangle className="h-5 w-5" /> },
    { endpoint: "/api/parse/ad2_12", title: "AD 2.12 - Runway Characteristics", description: "Click each runway to see details", icon: <Ruler className="h-5 w-5" /> },
    { endpoint: "/api/parse/ad2_13", title: "AD 2.13 - Declared Distances", description: "Click each runway to see distances", icon: <Navigation className="h-5 w-5" /> },
  ]

  if (enabled && (elementsLoading || (elements === null && !elementsError))) {
    return (
      <div className="grid gap-6">
        <Card className="bg-zinc-950 border-zinc-800 p-8">
          <p className="text-muted-foreground">Loading PDF elements (one Unstructured call)…</p>
          <TableSkeleton />
        </Card>
      </div>
    )
  }
  if (enabled && elementsError) {
    return (
      <div className="text-red-400 flex items-center gap-2">
        <AlertCircle className="h-5 w-5" />
        <p>{elementsError}</p>
      </div>
    )
  }

  return (
    <div className="grid gap-6">
      {tables.map((table) => (
        <DataTable
          key={table.endpoint}
          endpoint={table.endpoint}
          title={table.title}
          description={table.description}
          icon={table.icon}
          enabled={enabled}
          fileId={fileId}
          elements={elements ?? undefined}
          elementsLoading={elementsLoading}
        />
      ))}
    </div>
  )
}
