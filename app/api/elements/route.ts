// app/api/elements/route.ts
import { NextResponse } from "next/server"
import { runPythonJson } from "@/app/api/_py"

export const runtime = "nodejs"

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const pdfUrl = body?.pdfUrl
    
    if (!pdfUrl || typeof pdfUrl !== "string") {
      return NextResponse.json(
        { success: false, error: "No pdfUrl provided" },
        { status: 400 }
      )
    }
    
    const code = `
import json, os, sys
from pathlib import Path

ROOT = Path(os.getcwd()).resolve()
sys.path.insert(0, str(ROOT / "lib"))

from pdf_to_elements import pdf_path_to_elements

pdf_path = sys.argv[1]   # URL هم اوکیه
tables = pdf_path_to_elements(pdf_path)

print(json.dumps(tables, ensure_ascii=False))
`
    
    const stdout = await runPythonJson({
      code,
      argv: [pdfUrl],
  })
    
    const tables = JSON.parse(stdout)
    
    return NextResponse.json({ success: true, tables })
  } catch (e: any) {
    return NextResponse.json(
      { success: false, error: e?.message || "Failed to load elements" },
      { status: 500 }
    )
  }
}