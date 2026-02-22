import { NextRequest, NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

export async function POST(request: NextRequest) {
  // Only use this route in development
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json(
      { error: 'Use Python function in production' },
      { status: 404 }
    )
  }

  try {
    const body = await request.json()
    const { pdfUrl } = body

    if (!pdfUrl || typeof pdfUrl !== 'string') {
      return NextResponse.json(
        { error: 'pdfUrl نامعتبر یا موجود نیست' },
        { status: 400 }
      )
    }

    // Escape the URL for shell safety
    const escapedUrl = pdfUrl.replace(/'/g, "'\"'\"'")
    
    const pythonCode = `
import json
import sys
import os
from pathlib import Path

ROOT = Path(os.getcwd()).resolve()
sys.path.insert(0, str(ROOT / 'lib'))

try:
    from pdf_to_elements import pdf_path_to_elements
    tables = pdf_path_to_elements('${escapedUrl}')
    print(json.dumps({'success': True, 'tables': tables}))
except Exception as e:
    print(json.dumps({'success': False, 'error': str(e)}))
`

    const { stdout, stderr } = await execAsync(`python3 -c "${pythonCode}"`)
    
    if (stderr) {
      console.error('Python stderr:', stderr)
    }

    try {
      const result = JSON.parse(stdout.trim())
      if (result.success) {
        return NextResponse.json(result)
      } else {
        return NextResponse.json(
          { error: result.error },
          { status: 500 }
        )
      }
    } catch (parseError) {
      return NextResponse.json(
        { error: `Failed to parse Python output: ${stdout}` },
        { status: 500 }
      )
    }

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