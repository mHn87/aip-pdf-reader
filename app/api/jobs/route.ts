import { NextResponse } from "next/server"
import { prisma } from "@/lib/db"

export async function GET() {
  try {
    const jobs = await prisma.job.findMany({
      orderBy: { createdAt: "desc" },
      take: 15,
      include: { _count: { select: { aips: true } } },
    })
    const list = jobs.map((j) => ({
      id: j.id,
      count: j.count,
      status: j.status,
      processedCount: j.processedCount,
      createdAt: j.createdAt.toISOString(),
      completedAt: j.completedAt?.toISOString() ?? null,
      durationMs: j.durationMs,
      errorMessage: j.errorMessage,
      urls: j.urls as string[],
    }))
    return NextResponse.json({ jobs: list })
  } catch (e) {
    console.error("jobs list:", e)
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Server error" },
      { status: 500 }
    )
  }
}

export async function DELETE() {
  try {
    await prisma.job.deleteMany({})
    return NextResponse.json({ success: true })
  } catch (e) {
    console.error("jobs delete all:", e)
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Server error" },
      { status: 500 }
    )
  }
}
