import { NextRequest, NextResponse } from 'next/server'
import { parsePdfUrl } from '@/lib/mineru'

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

    const tables = await parsePdfUrl(pdfUrl)
    return NextResponse.json({
      success: true,
      tables: { AD_2_10: tables.AD_2_10, AD_2_12: tables.AD_2_12 },
    })

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    console.error("pdf-to-elements error:", message, error)
    const isNetwork =
      message.includes("fetch failed") ||
      message.includes("ECONNREFUSED") ||
      message.includes("ENOTFOUND") ||
      message.includes("ZIP download")
    return NextResponse.json(
      {
        error: isNetwork
          ? `${message} — در صورت تکرار، اتصال به MinerU یا CDN از شبکه/سرور شما مسدود است. (امتحان VPN یا اجرای لوکال.)`
          : message.startsWith("[") ? message : `Server error: ${message}`,
      },
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