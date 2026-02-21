import { NextResponse } from "next/server"

export const runtime = "nodejs"

function arrayBufferToBase64(buffer: ArrayBuffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ""
  const chunkSize = 0x8000
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize))
  }
  return Buffer.from(binary, "binary").toString("base64")
}

export async function POST(req: Request) {
  try {
    const formData = await req.formData()
    const file = formData.get("file")
    if (!(file instanceof File)) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 })
    }
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      return NextResponse.json({ error: "Only PDF files are allowed" }, { status: 400 })
    }

    const fileData = arrayBufferToBase64(await file.arrayBuffer())
    const fileId =
      (globalThis.crypto && "randomUUID" in globalThis.crypto && globalThis.crypto.randomUUID()) ||
      `${Date.now()}-${Math.random().toString(16).slice(2)}`

    return NextResponse.json({
      success: true,
      filename: file.name,
      fileId,
      fileData,
    })
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || "Upload failed" }, { status: 500 })
  }
}

