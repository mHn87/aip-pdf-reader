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
      aips: job.aips.map((a) => ({
        id: a.id,
        name: a.name,
        status: a.status,
        createdAt: a.createdAt.toISOString(),
      })),
    })
  } catch (e) {
    console.error("job get:", e)
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Server error" },
      { status: 500 }
    )
  }
}
