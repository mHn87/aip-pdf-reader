"use client"

import { useState, useCallback, useRef } from "react"
import { Upload, FileText, X, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

interface PdfUploaderProps {
  onUploadSuccess: (filename: string) => void
  onClear: () => void
  uploadedFile: string | null
}

export function PdfUploader({ onUploadSuccess, onClear, uploadedFile }: PdfUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const uploadFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are allowed')
      return
    }

    setIsUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      // Create AbortController for timeout (10 minutes for large files)
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000)

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Upload failed' }))
        throw new Error(errorData.error || errorData.detail || 'Upload failed')
      }

      const data = await response.json()
      onUploadSuccess(data.filename)
    } catch (error: any) {
      if (error.name === 'AbortError') {
        setError('Upload timeout. The file might be too large. Please try again.')
      } else {
        setError(error.message || 'Failed to upload PDF. Please try again.')
      }
    } finally {
      setIsUploading(false)
    }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      uploadFile(file)
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadFile(file)
    }
  }

  const handleClear = async () => {
    try {
      await fetch('/api/clear', { method: 'DELETE' })
      onClear()
    } catch {
      console.error('Failed to clear upload')
    }
  }

  if (uploadedFile) {
    return (
      <Card className="border-dashed border-2 border-border">
        <CardContent className="flex flex-col items-center justify-center py-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-full bg-green-500/10">
              <FileText className="h-8 w-8 text-green-500" />
            </div>
            <div>
              <p className="font-medium">{uploadedFile}</p>
              <p className="text-sm text-muted-foreground">PDF uploaded successfully</p>
            </div>
          </div>
          <Button variant="outline" onClick={handleClear} className="gap-2">
            <X className="h-4 w-4" />
            Upload Different PDF
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card
      className={`border-dashed border-2 transition-colors ${
        isDragging ? 'border-primary bg-primary/5' : 'border-border'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <CardContent className="flex flex-col items-center justify-center py-16">
        {isUploading ? (
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-12 w-12 animate-spin text-muted-foreground" />
            <p className="text-muted-foreground">Uploading PDF...</p>
          </div>
        ) : (
          <>
            <div className="p-4 rounded-full bg-muted mb-4">
              <Upload className="h-10 w-10 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-medium mb-2">Upload AIP PDF</h3>
            <p className="text-sm text-muted-foreground mb-6 text-center">
              Drag and drop your PDF file here, or click to browse
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              className="gap-2"
            >
              <Upload className="h-4 w-4" />
              Select PDF File
            </Button>
            {error && (
              <p className="mt-4 text-sm text-destructive-foreground">{error}</p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
