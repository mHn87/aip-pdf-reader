import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/db"
import { createHash } from "crypto"

/** Check if URL returns a PDF (Content-Type). */
async function isPdfUrl(url: string): Promise<boolean> {
  try {
    const res = await fetch(url, { method: "HEAD", signal: AbortSignal.timeout(10000) })
    const ct = res.headers.get("content-type") || ""
    return res.ok && (ct.includes("application/pdf") || ct.includes("application/octet-stream"))
  } catch {
    return false
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const urls = body?.urls
    if (!Array.isArray(urls) || urls.length === 0) {
      return NextResponse.json({ error: "urls array is required" }, { status: 400 })
    }
    const list = urls.map((u: unknown) => (typeof u === "string" ? u.trim() : "")).filter(Boolean)
    if (list.length === 0) {
      return NextResponse.json({ error: "At least one URL required" }, { status: 400 })
    }

    for (const url of list) {
      const ok = await isPdfUrl(url)
      if (!ok) {
        return NextResponse.json(
          { error: `Not a PDF or unreachable: ${url.slice(0, 60)}...` },
          { status: 400 }
        )
      }
    }

    const jobId = createHash("sha256")
      .update(`${Date.now()}-${list.join(",")}`)
      .digest("hex")
      .slice(0, 12)

    await prisma.job.create({
      data: {
        id: jobId,
        count: list.length,
        urls: list,
        status: "pending",
        processedCount: 0,
      },
    })

    return NextResponse.json({ success: true, jobId }, { status: 200 })
  } catch (e) {
    console.error("validate-and-create:", e)
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Server error" },
      { status: 500 }
    )
  }
}
