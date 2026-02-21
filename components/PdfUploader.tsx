"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {  Link2 } from "lucide-react"

interface Props {
  onSuccess: (filename: string, fileId: string) => void
}

export function PdfUrlInput({ onSuccess }: Props) {
  const [url, setUrl] = useState("")
  
  const handleParse = async () => {
    if (!url) return
    
    onSuccess("", url)
  }
  
  return (
    <div className="flex gap-3">
      <input
        placeholder="AIP URL..."
        value={url}
        style={{
          color: "black"
        }}
        onChange={(e) => setUrl(e.target.value)}
      />
      
      <Button onClick={handleParse}  >
          <Link2 className="h-4 w-4" />
        Parse
      </Button>
      
    </div>
  )
}