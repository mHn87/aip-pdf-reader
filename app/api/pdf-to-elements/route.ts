import { NextRequest, NextResponse } from 'next/server'
import JSZip from 'jszip'

// MinerU API integration
const TOKEN = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI0NjkwMDgwNiIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc3MTE4NTg2NywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiNmI0OWI0OWQtMWEzZi00MmQ5LWJlY2MtMTViMGJhNzA0MWY3IiwiZW1haWwiOiIiLCJleHAiOjE3Nzg5NjE4Njd9.1xihdazAQG9trnRIub0vZ7h41yy-PvcIk_swXSFM8sI5lIA1WexSTpvtk0R5DXI-ujmcbeX8MYRG9pGV7AvVRw"
const CREATE_URL = "https://mineru.net/api/v4/extract/task"
const HEADERS = {
  "Content-Type": "application/json", 
  "Authorization": `Bearer ${TOKEN}`
}

async function createTask(pdfPath: string) {
  const payload = {
    url: pdfPath,
    model_version: "vlm",
    output_format: "json",
    extract_config: {
      enable_ocr: false,
      enable_image: false,
      enable_formula: false
    }
  }
  
  const res = await fetch(CREATE_URL, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify(payload)
  })
  
  const data = await res.json()
  if (!data.data || !data.data.task_id) {
    throw new Error(`API did not return task_id: ${JSON.stringify(data)}`)
  }
  return data.data.task_id
}

async function waitForResult(taskId: string, timeout = 300000) {
  const url = `https://mineru.net/api/v4/extract/task/${taskId}`
  const start = Date.now()
  
  while (true) {
    const r = await fetch(url, { headers: HEADERS })
    const data = await r.json()
    const result = data.data || {}
    const state = result.state
    
    if (state === "done" || state === "success") {
      return result
    }
    if (state === "failed" || state === "error") {
      throw new Error(result.err_msg || "Task failed")
    }
    if (Date.now() - start > timeout) {
      throw new Error("Timeout waiting for task")
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000))
  }
}

async function downloadAndExtractZip(zipUrl: string) {
  const r = await fetch(zipUrl)
  const buffer = await r.arrayBuffer()
  
  const zip = new JSZip()
  const zipData = await zip.loadAsync(buffer)
  
  const extracted: Record<string, string> = {}
  
  for (const [filename, file] of Object.entries(zipData.files)) {
    if (filename.endsWith('_content_list.json')) {
      const content = await file.async('text')
      extracted[filename] = content
    }
  }
  
  return extracted
}

function extractAdTables(extractedJsons: Record<string, string>) {
  const ad_2_10: string[] = []
  const ad_2_12: string[] = []

  for (const contentStr of Object.values(extractedJsons)) {
    try {
      const data = JSON.parse(contentStr)
      const items = Array.isArray(data) ? data : (data.items || [])
      
      for (let idx = 0; idx < items.length; idx++) {
        const item = items[idx]
        if (item.type !== "table") continue
        
        const captions = item.table_caption || []
        const captionText = captions.join(" ").toUpperCase()
        
        let prevText = ""
        if (idx > 0 && items[idx-1].type === "text") {
          prevText = (items[idx-1].text || "").toUpperCase()
        }
        
        const combined = prevText + " " + captionText
        const html = item.table_body || ""
        
        if (combined.includes("AD 2.10")) {
          ad_2_10.push(html)
        } else if (combined.includes("AD 2.12")) {
          ad_2_12.push(html)
        }
      }
    } catch (e) {
      console.error("Error parsing JSON:", e)
    }
  }

  return { AD_2_10: ad_2_10, AD_2_12: ad_2_12 }
}

async function pdfPathToElements(pdfPath: string) {
  const taskId = await createTask(pdfPath)
  const result = await waitForResult(taskId)
  const zipUrl = result.full_zip_url
  
  if (!zipUrl) {
    throw new Error("No ZIP URL found")
  }
  
  const extractedJsons = await downloadAndExtractZip(zipUrl)
  const tables = extractAdTables(extractedJsons)
  return tables
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { pdfUrl } = body

    if (!pdfUrl || typeof pdfUrl !== 'string') {
      return NextResponse.json(
        { error: 'pdfUrl نامعتبر یا موجود نیست' },
        { status: 400 }
      )
    }

    const tables = await pdfPathToElements(pdfUrl)
    
    return NextResponse.json({
      success: true,
      tables
    })

  } catch (error) {
    console.error('API Error:', error)
    return NextResponse.json(
      { error: `Server error: ${error}` },
      { status: 500 }
    )
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  })
}