import { NextRequest, NextResponse } from "next/server"

// OpenRouter: یک API برای صدها مدل (مستندات: https://openrouter.ai/docs/quickstart)
const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
// مدل رایگان چت (از لیست فعلی OpenRouter). در .env: OPENROUTER_EXTRACT_MODEL=...
const EXTRACT_MODEL = process.env.OPENROUTER_EXTRACT_MODEL || "google/gemma-3-4b-it:free"

const SYSTEM_PROMPT = `You are an expert aeronautical data extractor.

TASK:
Extract ONLY the obstacles related to "In approach / TKOF areas" from AD 2.10 and return the result grouped by runway/area.

OUTPUT REQUIREMENTS:

1. Extract ONLY from the "In approach / TKOF areas" section.
   Ignore "In circling area and at AD".

2. Normalize and TRIM all values:
   - remove extra spaces
   - remove line breaks
   - collapse multiple spaces
   - no leading/trailing whitespace

3. RWY/Area affected SPLITTING RULES:

   If a cell contains multiple runway/area pairs such as:
   "31R / APCH 13L / TKOF"

   You MUST output TWO separate logical records:
   - 31R / APCH
   - 13L / TKOF

   Duplicate obstacle data for each produced record.

4. RUNWAY SIDE EXPANSION RULES:

   If runway has both sides combined, e.g.:
   "14R/L / APCH"

   You MUST expand into:
   - 14R / APCH
   - 14L / APCH

   If runway number has no side, e.g.:
   "31 / APCH"

   You MUST expand into:
   - 31R / APCH
   - 31L / APCH

   If written like:
   "31R / L APCH"

   You MUST normalize and expand into:
   - 31R / APCH
   - 31L / APCH

5. TABLE ROBUSTNESS:

   The source table may be messy:
   - headers may be broken across lines
   - columns may shift
   - rows may wrap
   - values may appear in adjacent cells

   You MUST reconstruct rows intelligently.

6. OUTPUT FORMAT (STRICT JSON — NO HTML):

   Return a JSON object grouped by RWY/Area affected.

   Structure:

   {
     "<RWY/Area affected>": [
       {
         "Obstacle type Elevation/ HGT Markings/LGT": "...",
         "Coordinates": "..."
       }
     ]
   }

7. GROUPING RULES:

   - Each RWY/Area affected is a key.
   - Multiple obstacles under same key must be in an array.
   - Preserve duplicates only if obstacle data differs.
   - Do NOT output empty objects.

8. If no valid data exists, return:

   {}

Return ONLY valid JSON. No explanations.`

export async function POST(request: NextRequest) {
  const apiKey = process.env.OPENROUTER_API_KEY ?? process.env.OPENAI_API_KEY
  if (!apiKey) {
    return NextResponse.json(
      { success: false, error: "OPENROUTER_API_KEY or OPENAI_API_KEY is not set" },
      { status: 500 }
    )
  }

  try {
    const body = await request.json()
    const tableHtml = body?.tableHtml ?? body?.table_html
    if (!tableHtml || typeof tableHtml !== "string") {
      return NextResponse.json(
        { success: false, error: "tableHtml is required" },
        { status: 400 }
      )
    }

    const res = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: EXTRACT_MODEL,
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          {
            role: "user",
            content: `Extract from this AD 2.10 HTML table. Return ONLY the JSON object as specified.\n\n${tableHtml}`,
          },
        ],
        response_format: { type: "json_object" },
        temperature: 0.1,
      }),
    })

    if (!res.ok) {
      const errText = await res.text()
      return NextResponse.json(
        { success: false, error: `OpenRouter API error: ${res.status} ${errText}` },
        { status: 502 }
      )
    }

    const data = await res.json()
    const content = data?.choices?.[0]?.message?.content
    if (!content) {
      return NextResponse.json(
        { success: false, error: "No content in model response" },
        { status: 502 }
      )
    }

    let extracted: Record<string, Array<{ "Obstacle type Elevation/ HGT Markings/LGT": string; Coordinates: string }>>
    try {
      extracted = JSON.parse(content.trim())
      if (extracted === null || typeof extracted !== "object" || Array.isArray(extracted)) {
        extracted = {}
      }
    } catch {
      return NextResponse.json(
        { success: false, error: "Model did not return valid JSON" },
        { status: 502 }
      )
    }

    return NextResponse.json({ success: true, data: extracted })
  } catch (e) {
    console.error("extract ad2-10:", e)
    return NextResponse.json(
      { success: false, error: e instanceof Error ? e.message : "Extract failed" },
      { status: 500 }
    )
  }
}
