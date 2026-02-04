"use client"

import { useState } from "react"
import { Navbar } from "@/components/Navbar"
import { PdfUploader } from "@/components/PdfUploader"
import { DataTables } from "@/components/DataTables"

export default function Home() {
  const [uploadedFile, setUploadedFile] = useState<string | null>(null)
  const [fileId, setFileId] = useState<string | null>(null)

  const handleUploadSuccess = (filename: string, id: string) => {
    setUploadedFile(filename)
    setFileId(id)
    // Store fileId in localStorage as backup
    if (typeof window !== 'undefined') {
      localStorage.setItem('aip_fileId', id)
    }
  }

  const handleClear = () => {
    setUploadedFile(null)
    setFileId(null)
    if (typeof window !== 'undefined') {
      localStorage.removeItem('aip_fileId')
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container max-w-screen-xl mx-auto px-4 py-8">
        {/* Header Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Import PDF</h1>
          <p className="text-muted-foreground">
            Upload an AIP (Aeronautical Information Publication) PDF to extract and view structured data
          </p>
        </div>

        {/* Upload Section */}
        <div className="mb-10">
          <PdfUploader
            onUploadSuccess={handleUploadSuccess}
            onClear={handleClear}
            uploadedFile={uploadedFile}
          />
        </div>

        {/* Data Tables Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-2">Extracted Data</h2>
          <p className="text-muted-foreground mb-6">
            {uploadedFile 
              ? `Showing parsed data from ${uploadedFile}`
              : "Data will appear here after uploading a PDF"
            }
          </p>
          <DataTables enabled={!!uploadedFile} fileId={fileId} />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6 mt-12">
        <div className="container max-w-screen-xl mx-auto px-4 text-center text-sm text-muted-foreground">
          AIP PDF Parser • Built with Next.js
        </div>
      </footer>
    </div>
  )
}
