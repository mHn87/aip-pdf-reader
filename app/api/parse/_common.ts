import { writeFile, unlink } from "node:fs/promises"
import { tmpdir } from "node:os"
import path from "node:path"
import { runPythonJson } from "@/app/api/_py"

export async function parseFromElements(opts: { extractorModule: string; extractorFn: string; elements: unknown }) {
  const tmpJson = path.join(tmpdir(), `aip_elements_${Date.now()}_${Math.random().toString(16).slice(2)}.json`)
  try {
    await writeFile(tmpJson, JSON.stringify(opts.elements))
    const code = `
import json, os, sys
from pathlib import Path
ROOT = Path(os.getcwd()).resolve()
sys.path.insert(0, str(ROOT))
mod = __import__(sys.argv[1], fromlist=[sys.argv[2]])
fn = getattr(mod, sys.argv[2])
with open(sys.argv[3], "r", encoding="utf-8") as f:
    elements = json.load(f)
out = fn(elements)
print(json.dumps(out, ensure_ascii=False))
`
    const stdout = await runPythonJson({ code, argv: [opts.extractorModule, opts.extractorFn, tmpJson] })
    return JSON.parse(stdout)
  } finally {
    try {
      await unlink(tmpJson)
    } catch {}
  }
}

