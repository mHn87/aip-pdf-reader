"use client"

import { useState } from "react"
import { PdfUrlInput } from "@/components/PdfUploader"
import { DataTables } from "@/components/DataTables"

export default function SingleParsePage() {
  const [fileId, setFileId] = useState<string | null>(null)

  const handleSuccess = (_filename: string, id: string) => setFileId(id)

  return (
    <div className="container max-w-screen-xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-xl md:text-2xl font-bold text-white mb-2">Single parse AIP</h1>
      <p className="text-zinc-400 mb-6">Enter one PDF URL and parse with MinerU.</p>
      <div className="mb-8">
        <PdfUrlInput onSuccess={handleSuccess} />
      </div>
      <DataTables url={fileId ?? ""} />
    </div>
  )
}
