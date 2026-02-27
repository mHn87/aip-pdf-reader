/**
 * قوانین تقسیم RWY/Area برای AD 2.10:
 * - "31R / APCH 13L / TKOF" → دو رکورد: "31R / APCH" و "13L / TKOF" با همان داده
 * - "31 / APCH" (بدون L/R) → هر دو "31R / APCH" و "31L / APCH"
 * - "31R / L APCH" (L به‌معنای چپ) → هر دو "31R / APCH" و "31L / APCH"
 */

export type ObstacleRow = {
  "Obstacle type Elevation/ HGT Markings/LGT": string
  Coordinates: string
}

export type Ad210Extract = Record<string, ObstacleRow[]>

const TRIM = (s: string) => (s ?? "").trim()

/**
 * یک مقدار RWY/Area را به لیست کلیدهای نهایی تبدیل می‌کند.
 * - "31 / APCH" → ["31R / APCH", "31L / APCH"]
 * - "31R / APCH 13L / TKOF" → ["31R / APCH", "13L / TKOF"]
 * - "31R / L APCH" → ["31R / APCH", "31L / APCH"]
 */
function expandRwyArea(rwyArea: string): string[] {
  const v = TRIM(rwyArea)
  if (!v) return []

  const result: string[] = []
  const seen = new Set<string>()

  // پیدا کردن همهٔ بخش‌های نوع "عدد + اختیاری R/L + / + نوع" (APCH, TKOF, L APCH, ...)
  const blockRegex = /(\d+)([RL]?)\s*\/\s*([A-Za-z\s\/]+?)(?=\s*\d+[RL]?\s*\/|$)/gi
  let m: RegExpExecArray | null
  while ((m = blockRegex.exec(v)) !== null) {
    const num = m[1]
    const lr = (m[2] || "").toUpperCase()
    const rest = TRIM(m[3])
    const suffix = ` / ${rest}`
    const add = (key: string) => {
      if (!seen.has(key)) {
        seen.add(key)
        result.push(key)
      }
    }
    if (lr === "R") {
      add(`${num}R${suffix}`)
    } else if (lr === "L") {
      add(`${num}L${suffix}`)
    } else {
      add(`${num}R${suffix}`)
      add(`${num}L${suffix}`)
    }
  }

  if (result.length > 0) return result
  return [v]
}

/**
 * آرایهٔ خام ردیف‌های استخراج‌شده (با ستون RWY/Area affected) را به آبجکت
 * کلید = RWY/Area، مقدار = آرایهٔ obstacles با همان قوانین تقسیم می‌کند.
 */
export function splitRwyAreas(
  rows: Array<{
    "RWY/Area affected"?: string
    "Obstacle type Elevation/ HGT Markings/LGT"?: string
    Coordinates?: string
  }>
): Ad210Extract {
  const out: Ad210Extract = {}

  for (const row of rows) {
    const rwyArea = TRIM(row["RWY/Area affected"] ?? "")
    const obstacle = TRIM(row["Obstacle type Elevation/ HGT Markings/LGT"] ?? "")
    const coords = TRIM(row["Coordinates"] ?? "")
    const entry: ObstacleRow = {
      "Obstacle type Elevation/ HGT Markings/LGT": obstacle,
      Coordinates: coords,
    }

    const keys = expandRwyArea(rwyArea)
    if (keys.length === 0) {
      const fallback = rwyArea || "Other"
      if (!out[fallback]) out[fallback] = []
      out[fallback].push(entry)
      continue
    }
    for (const key of keys) {
      if (!out[key]) out[key] = []
      out[key].push(entry)
    }
  }

  return out
}
