import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/db"

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  try {
    const aip = await prisma.aip.findUnique({
      where: { id },
      include: { job: true },
    })
    if (!aip) return NextResponse.json({ error: "AIP not found" }, { status: 404 })
    const urls = (aip.job?.urls as string[]) || []
    const sourceUrl =
      typeof aip.urlIndex === "number" && aip.urlIndex >= 0 && aip.urlIndex < urls.length
        ? urls[aip.urlIndex]
        : undefined
    return NextResponse.json({
      id: aip.id,
      name: aip.name,
      status: aip.status,
      runways: aip.runways,
      obstacles: aip.obstacles,
      createdAt: aip.createdAt.toISOString(),
      jobId: aip.jobId,
      sourceUrl,
    })
  } catch (e) {
    console.error("aip get:", e)
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Server error" },
      { status: 500 }
    )
  }
}
