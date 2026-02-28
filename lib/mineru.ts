import JSZip from "jszip"

const TOKEN =
  "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI0NjkwMDgwNiIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc3MTE4NTg2NywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiNmI0OWI0OWQtMWEzZi00MmQ5LWJlY2MtMTViMGJhNzA0MWY3IiwiZW1haWwiOiIiLCJleHAiOjE3Nzg5NjE4Njd9.1xihdazAQG9trnRIub0vZ7h41yy-PvcIk_swXSFM8sI5lIA1WexSTpvtk0R5DXI-ujmcbeX8MYRG9pGV7AvVRw"
const CREATE_URL = "https://mineru.net/api/v4/extract/task"
const HEADERS = {
  "Content-Type": "application/json",
  Authorization: `Bearer ${TOKEN}`,
}

const ZIP_TIMEOUT_MS = 360000 // 6 min for slow CDNs
const ZIP_FETCH_OPTIONS = {
  headers: {
    "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    Accept: "application/zip,*/*",
  },
  signal: AbortSignal.timeout(ZIP_TIMEOUT_MS),
} as const

export type MinerUTables = { AD_2_10: string[]; AD_2_12: string[] }

const CREATE_TASK_TIMEOUT_MS = 90000 // 1.5 min
async function createTask(pdfPath: string) {
  const res = await fetch(CREATE_URL, {
    method: "POST",
    headers: HEADERS,
    body: JSON.stringify({
      url: pdfPath,
      model_version: "vlm",
      output_format: "json",
      extract_config: { enable_ocr: false, enable_image: false, enable_formula: false },
    }),
    signal: AbortSignal.timeout(CREATE_TASK_TIMEOUT_MS),
  })
  const data = await res.json()
  if (!data.data?.task_id) throw new Error(`MinerU: no task_id: ${JSON.stringify(data)}`)
  return data.data.task_id as string
}

const WAIT_FOR_RESULT_TIMEOUT_MS = 600000 // 10 min total for MinerU processing
const POLL_FETCH_TIMEOUT_MS = 30000 // 30s per status check
async function waitForResult(taskId: string, timeout = WAIT_FOR_RESULT_TIMEOUT_MS) {
  const url = `https://mineru.net/api/v4/extract/task/${taskId}`
  const start = Date.now()
  while (true) {
    const r = await fetch(url, {
      headers: HEADERS,
      signal: AbortSignal.timeout(POLL_FETCH_TIMEOUT_MS),
    })
    const data = await r.json()
    const result = data.data || {}
    const state = result.state
    if (state === "done" || state === "success") return result as { full_zip_url?: string }
    if (state === "failed" || state === "error") throw new Error(result.err_msg || "Task failed")
    if (Date.now() - start > timeout) throw new Error("Timeout waiting for task")
    await new Promise((r) => setTimeout(r, 5000))
  }
}

async function downloadAndExtractZip(zipUrl: string) {
  let r: Response
  try {
    r = await fetch(zipUrl, ZIP_FETCH_OPTIONS)
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    await new Promise((r) => setTimeout(r, 2000))
    r = await fetch(zipUrl, ZIP_FETCH_OPTIONS)
  }
  if (!r.ok) throw new Error(`ZIP download: ${r.status} ${r.statusText}`)
  const buffer = await r.arrayBuffer()
  const zip = new JSZip()
  const zipData = await zip.loadAsync(buffer)
  const extracted: Record<string, string> = {}
  for (const [filename, file] of Object.entries(zipData.files)) {
    if (file.dir) continue
    if (
      filename.endsWith("_content_list.json") ||
      (filename.endsWith(".json") && filename.includes("content"))
    ) {
      const content = await file.async("text")
      extracted[filename] = content
    }
  }
  return extracted
}

function extractAdTables(extractedJsons: Record<string, string>): MinerUTables {
  const ad_2_10: string[] = []
  const ad_2_12: string[] = []
  for (const contentStr of Object.values(extractedJsons)) {
    try {
      const data = JSON.parse(contentStr) as { items?: unknown[] }
      const items = Array.isArray(data) ? data : (data.items || [])
      for (let idx = 0; idx < items.length; idx++) {
        const item = items[idx] as { type?: string; table_caption?: string[]; table_body?: string; text?: string } | null
        if (!item || typeof item !== "object" || item.type !== "table") continue
        const captions = item.table_caption || []
        const captionText = captions.join(" ").toUpperCase()
        const prevText =
          idx > 0 && items[idx - 1] && typeof items[idx - 1] === "object" && (items[idx - 1] as { type?: string }).type === "text"
            ? ((items[idx - 1] as { text?: string }).text || "").toUpperCase()
            : ""
        const combined = prevText + " " + captionText
        const html = (item.table_body || "").trim()
        const htmlUpper = html.toUpperCase()
        const isAd210 =
          combined.includes("AD 2.10") ||
          (combined.includes("2.10") && combined.includes("OBSTACLE")) ||
          (htmlUpper.includes("IN APPROACH") && htmlUpper.includes("RWY/AREA"))
        const isAd212 =
          combined.includes("AD 2.12") ||
          (combined.includes("2.12") && combined.includes("RUNWAY"))
        if (isAd210 && html) ad_2_10.push(html)
        else if (isAd212 && html) ad_2_12.push(html)
      }
    } catch {
      // skip
    }
  }
  return { AD_2_10: ad_2_10, AD_2_12: ad_2_12 }
}

/** Parse one PDF URL via MinerU and return AD 2.10 / AD 2.12 tables. */
export async function parsePdfUrl(pdfUrl: string): Promise<MinerUTables> {
  const taskId = await createTask(pdfUrl)
  const result = await waitForResult(taskId)
  const zipUrl = result.full_zip_url
  if (!zipUrl) throw new Error("MinerU: no ZIP URL")
  const extractedJsons = await downloadAndExtractZip(zipUrl)
  return extractAdTables(extractedJsons)
}

/** Derive AIP name from URL (e.g. .../OIAD.pdf/... -> OIAD). */
export function aipNameFromUrl(url: string): string {
  try {
    const path = new URL(url).pathname
    const match = path.match(/\/([A-Z0-9]{4})\.pdf/i) || path.match(/\/([A-Z0-9]{4})\.PDF/i)
    return match ? match[1].toUpperCase() : "AIP"
  } catch {
    return "AIP"
  }
}
