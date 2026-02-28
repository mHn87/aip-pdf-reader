import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/db"

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params
  try {
    const job = await prisma.job.findUnique({
      where: { id: jobId },
      include: { aips: true },
    })
    if (!job) return NextResponse.json({ error: "Job not found" }, { status: 404 })
    const aipsWithCounts = job.aips.map((a) => {
      const obstacles = (a.obstacles as Record<string, unknown>) ?? null
      const runways = (a.runways as Record<string, unknown>) ?? null
      return {
        id: a.id,
        name: a.name,
        status: a.status,
        createdAt: a.createdAt.toISOString(),
        obstaclesCount: obstacles ? Object.keys(obstacles).length : 0,
        runwaysCount: runways ? Object.keys(runways).length : 0,
      }
    })

    return NextResponse.json({
      id: job.id,
      count: job.count,
      urls: job.urls as string[],
      status: job.status,
      processedCount: job.processedCount,
      createdAt: job.createdAt.toISOString(),
      completedAt: job.completedAt?.toISOString() ?? null,
      durationMs: job.durationMs,
      errorMessage: job.errorMessage,
      aips: aipsWithCounts,
    })
  } catch (e) {
    console.error("job get:", e)
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Server error" },
      { status: 500 }
    )
  }
}
