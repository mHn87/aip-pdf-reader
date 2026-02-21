import { NextResponse } from "next/server"
import { parseFromElements } from "@/app/api/parse/_common"

export const runtime = "nodejs"

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const elements = body?.elements
    if (!Array.isArray(elements)) {
      return NextResponse.json({ success: false, error: "No elements provided" }, { status: 400 })
    }
    const data = await parseFromElements({
      extractorModule: "ad2_10_from_elements",
      extractorFn: "extract_ad2_10_from_elements",
      elements,
    })
    return NextResponse.json({ success: true, data })
  } catch (e: any) {
    return NextResponse.json({ success: false, error: e?.message || "Parse failed" }, { status: 500 })
  }
}

