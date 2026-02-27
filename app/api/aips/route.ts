import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/db"

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const jobId = searchParams.get("jobId")

    const where = jobId ? { jobId, status: { in: ["success", "pending"] } } : { status: { in: ["success", "pending"] } }

    const aips = await prisma.aip.findMany({
      where,
      orderBy: { createdAt: "desc" },
      take: 100,
    })

    const list = aips.map((a) => ({
      id: a.id,
      name: a.name,
      status: a.status,
      createdAt: a.createdAt.toISOString(),
      jobId: a.jobId,
    }))

    return NextResponse.json({ aips: list })
  } catch (e) {
    console.error("aips list:", e)
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Server error" },
      { status: 500 }
    )
  }
}

export async function DELETE() {
  try {
    await prisma.aip.deleteMany({})
    return NextResponse.json({ success: true })
  } catch (e) {
    console.error("aips delete all:", e)
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Server error" },
      { status: 500 }
    )
  }
}
