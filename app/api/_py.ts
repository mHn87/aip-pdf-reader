import { execFile } from "node:child_process"
import { promisify } from "node:util"

const execFileAsync = promisify(execFile)

export async function runPythonJson(args: { code: string; argv: string[] }) {
  const { stdout, stderr } = await execFileAsync("python3", ["-c", args.code, ...args.argv], {
    maxBuffer: 1024 * 1024 * 200, // up to ~200MB of stdout
    env: process.env,
  })
  if (stderr && stderr.trim()) {
    // بعضی libها روی stderr warning می‌نویسن؛ ولی اگر JSON سالم برگشت مشکلی نیست.
  }
  return stdout
}

