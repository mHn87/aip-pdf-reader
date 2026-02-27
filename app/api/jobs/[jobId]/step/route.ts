import { NextRequest, NextResponse } from "next/server"
import { prisma } from "@/lib/db"
import { parsePdfUrl, aipNameFromUrl } from "@/lib/mineru"

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params
  try {
    const job = await prisma.job.findUnique({ where: { id: jobId }, include: { aips: true } })
    if (!job) return NextResponse.json({ error: "Job not found" }, { status: 404 })
    if (job.status !== "pending") {
      return NextResponse.json({ job: job, message: "Job already completed or failed" }, { status: 200 })
    }

    const urls = job.urls as string[]
    const index = job.processedCount
    if (index >= urls.length) {
      const completedAt = new Date()
      const durationMs = job.createdAt ? completedAt.getTime() - job.createdAt.getTime() : null
      await prisma.job.update({
        where: { id: jobId },
        data: { status: "success", completedAt, durationMs },
      })
      return NextResponse.json({ jobId, status: "success", processedCount: index }, { status: 200 })
    }

    const pdfUrl = urls[index]
    const name = aipNameFromUrl(pdfUrl)

    try {
      const tables = await parsePdfUrl(pdfUrl)
      const runways: Record<string, { parse: string; extract: null }> = {}
      const obstacles: Record<string, { parse: string; extract: null }> = {}
      if (tables.AD_2_12?.length) {
        tables.AD_2_12.forEach((html, i) => {
          runways[`ad 2_${i + 1}`] = { parse: html, extract: null }
        })
      }
      if (tables.AD_2_10?.length) {
        tables.AD_2_10.forEach((html, i) => {
          obstacles[`ad 2_${i + 1}`] = { parse: html, extract: null }
        })
      }

      await prisma.aip.create({
        data: {
          jobId,
          status: "success",
          name,
          runways: Object.keys(runways).length ? (runways as object) : undefined,
          obstacles: Object.keys(obstacles).length ? (obstacles as object) : undefined,
          urlIndex: index,
        },
      })

      const newProcessed = index + 1
      if (newProcessed >= urls.length) {
        const completedAt = new Date()
        const durationMs = job.createdAt ? completedAt.getTime() - job.createdAt.getTime() : null
        await prisma.job.update({
          where: { id: jobId },
          data: { status: "success", processedCount: newProcessed, completedAt, durationMs },
        })
      } else {
        await prisma.job.update({
          where: { id: jobId },
          data: { processedCount: newProcessed },
        })
      }

      const updated = await prisma.job.findUnique({ where: { id: jobId } })
      return NextResponse.json({
        jobId,
        status: updated?.status ?? "pending",
        processedCount: newProcessed,
        currentName: name,
      })
    } catch (parseError) {
      const msg = parseError instanceof Error ? parseError.message : String(parseError)
      await prisma.aip.deleteMany({ where: { jobId } })
      await prisma.job.update({
        where: { id: jobId },
        data: { status: "error", errorMessage: msg, completedAt: new Date() },
      })
      return NextResponse.json(
        { jobId, status: "error", error: msg, processedCount: index },
        { status: 200 }
      )
    }
  } catch (e) {
    console.error("job step:", e)
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Server error" },
      { status: 500 }
    )
  }
}
