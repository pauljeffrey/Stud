"use client"

import { Document, Page, pdfjs } from "react-pdf"
import "react-pdf/dist/Page/AnnotationLayer.css"
import "react-pdf/dist/Page/TextLayer.css"
import { Loader2 } from "lucide-react"

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

type StudyPdfPanelProps = {
  file: File
  pageNumber: number
  onLoadSuccess: (info: { numPages: number }) => void
}

export function StudyPdfPanel({ file, pageNumber, onLoadSuccess }: StudyPdfPanelProps) {
  return (
    <Document
      file={file}
      onLoadSuccess={onLoadSuccess}
      loading={<Loader2 className="animate-spin text-purple-400" />}
    >
      <Page
        pageNumber={pageNumber}
        renderTextLayer={true}
        renderAnnotationLayer={true}
        className="border border-purple-700/40 rounded"
      />
    </Document>
  )
}
