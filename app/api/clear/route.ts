import { NextResponse } from "next/server"

export const runtime = "nodejs"

export async function DELETE() {
  // لوکال: چیزی روی سرور نگه نمی‌داریم. کلیر واقعی در فرانت (localStorage) انجام می‌شود.
  return NextResponse.json({ success: true })
}

