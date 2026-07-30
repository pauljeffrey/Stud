"use client"

import { useEffect, useState } from "react"
import { FileText, Search, Loader2, Globe2 } from "lucide-react"
import { apiFetch } from "@/app/lib/auth"
import { Input } from "@/app/components/ui/input"

export interface PickerDoc {
  id: string
  file_name: string
  processed?: boolean
  scope?: string
}

/**
 * Shared "browse before you upload" picker: shows the shared central library
 * first, then the caller's own documents. Selecting a document is the only
 * job of this component — upload stays wherever the page already has it.
 */
export function DocumentPicker({
  selectedId,
  onSelect,
  className,
}: {
  selectedId?: string | null
  onSelect: (doc: PickerDoc) => void
  className?: string
}) {
  const [library, setLibrary] = useState<PickerDoc[]>([])
  const [own, setOwn] = useState<PickerDoc[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([
      fetch("/api/learning/documents/library")
        .then((r) => (r.ok ? r.json() : { documents: [] }))
        .catch(() => ({ documents: [] })),
      apiFetch("/api/learning/documents")
        .then((r) => (r.ok ? r.json() : { documents: [] }))
        .catch(() => ({ documents: [] })),
    ]).then(([lib, mine]) => {
      if (cancelled) return
      setLibrary(lib.documents || [])
      setOwn(mine.documents || [])
      setLoading(false)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const q = search.toLowerCase()
  const filteredLibrary = library.filter((d) => d.file_name.toLowerCase().includes(q))
  const filteredOwn = own.filter((d) => d.file_name.toLowerCase().includes(q))

  return (
    <div className={className}>
      <p className="flex items-start gap-1.5 text-xs text-purple-300 mb-2">
        <Search className="h-3.5 w-3.5 shrink-0 mt-0.5" />
        Check our central library before uploading your own copy — it avoids processing the same
        document twice.
      </p>
      <Input
        placeholder="Search documents..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="bg-black/50 border-purple-700/40 text-xs h-8 mb-2"
      />
      {loading ? (
        <div className="flex items-center gap-2 text-gray-400 py-2 text-sm">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading documents...
        </div>
      ) : (
        <div className="max-h-56 overflow-y-auto space-y-3 border border-purple-700/40 rounded-lg bg-black/40 p-2">
          <div>
            <p className="text-[11px] uppercase tracking-wide text-purple-400 mb-1 flex items-center gap-1 px-1">
              <Globe2 className="h-3 w-3" /> Central Library
            </p>
            {filteredLibrary.length === 0 ? (
              <p className="text-xs text-gray-500 px-2 py-1">No matching library documents.</p>
            ) : (
              filteredLibrary.map((doc) => (
                <button
                  key={doc.id}
                  type="button"
                  onClick={() => onSelect(doc)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm truncate transition-colors ${
                    selectedId === doc.id
                      ? "bg-purple-700/50 border border-purple-500"
                      : "hover:bg-purple-900/30 border border-transparent"
                  }`}
                >
                  <FileText className="h-4 w-4 inline mr-2 text-purple-400" />
                  {doc.file_name}
                </button>
              ))
            )}
          </div>
          <div>
            <p className="text-[11px] uppercase tracking-wide text-purple-400 mb-1 px-1">
              Your Documents
            </p>
            {filteredOwn.length === 0 ? (
              <p className="text-xs text-gray-500 px-2 py-1">No documents uploaded yet.</p>
            ) : (
              filteredOwn.map((doc) => {
                const ready = doc.processed
                return (
                  <button
                    key={doc.id}
                    type="button"
                    disabled={!ready}
                    onClick={() => ready && onSelect(doc)}
                    className={`w-full text-left px-3 py-2 rounded-md text-sm truncate transition-colors flex items-center justify-between gap-2 ${
                      !ready
                        ? "opacity-50 cursor-not-allowed"
                        : selectedId === doc.id
                          ? "bg-purple-700/50 border border-purple-500"
                          : "hover:bg-purple-900/30 border border-transparent"
                    }`}
                  >
                    <span className="truncate">
                      <FileText className="h-4 w-4 inline mr-2 text-purple-400" />
                      {doc.file_name}
                    </span>
                    {!ready && (
                      <span className="text-[10px] text-purple-300 shrink-0 flex items-center gap-1">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Processing
                      </span>
                    )}
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
