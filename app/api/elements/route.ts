// app/api/elements/route.ts
import { NextResponse } from "next/server"
import { writeFile, unlink } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { runPythonJson } from "@/app/api/_py"

export const runtime = "nodejs"

export async function POST(req: Request) {
  let tmpPdfPath: string | null = null
  try {
    const body = await req.json()
    const fileData = body?.fileData
    if (!fileData || typeof fileData !== "string") {
      return NextResponse.json({ success: false, error: "No fileData provided" }, { status: 400 })
    }
    
    // ذخیره PDF در مسیر موقت
    const pdfBuffer = Buffer.from(fileData, "base64")
    tmpPdfPath = path.join(tmpdir(), `aip_elements_${Date.now()}.pdf`)
    await writeFile(tmpPdfPath, pdfBuffer)
    
    // کد پایتون: مسیر lib/ را اضافه می‌کنیم
    const code = `
import json, os, sys
from pathlib import Path

ROOT = Path(os.getcwd()).resolve()
sys.path.insert(0, str(ROOT / "lib"))  # مسیر lib اضافه شد

from pdf_to_elements import pdf_path_to_elements

pdf_path = sys.argv[1]
tables = pdf_path_to_elements(pdf_path)
print(json.dumps(tables, ensure_ascii=False))
`
    
    const stdout = await runPythonJson({ code, argv: [tmpPdfPath] })
    const tables = JSON.parse(stdout)
    
    return NextResponse.json({ success: true, tables })
  } catch (e: any) {
    return NextResponse.json({ success: false, error: e?.message || "Failed to load elements" }, { status: 500 })
  } finally {
    if (tmpPdfPath) {
      try {
        await unlink(tmpPdfPath)
      } catch {}
    }
  }
}