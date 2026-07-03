'use client'

import React, { useState, useRef, useCallback } from 'react'
import { Upload, FileUp, CheckCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { casesApi } from '@/lib/api'
import type { UploadResponse } from '@/types'

interface UploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onUploadComplete: () => void
}

export function UploadDialog({ open, onOpenChange, onUploadComplete }: UploadDialogProps) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<UploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showErrors, setShowErrors] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const reset = useCallback(() => {
    setFile(null)
    setResult(null)
    setError(null)
    setShowErrors(false)
    setDragOver(false)
  }, [])

  const handleOpenChange = useCallback(
    (newOpen: boolean) => {
      if (!newOpen) reset()
      onOpenChange(newOpen)
    },
    [onOpenChange, reset]
  )

  const handleFileSelect = useCallback((selectedFile: File) => {
    setFile(selectedFile)
    setResult(null)
    setError(null)
  }, [])

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0]
      if (f) handleFileSelect(f)
    },
    [handleFileSelect]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const f = e.dataTransfer.files[0]
      if (f && (f.name.endsWith('.csv') || f.name.endsWith('.json'))) {
        handleFileSelect(f)
      }
    },
    [handleFileSelect]
  )

  const handleUpload = useCallback(async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const res = await casesApi.upload(file)
      setResult(res.data)
      onUploadComplete()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } }
        setError(axiosErr.response?.data?.detail || 'Upload failed')
      } else {
        setError('Upload failed. Check your connection and try again.')
      }
    } finally {
      setUploading(false)
    }
  }, [file, onUploadComplete])

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Upload Test Cases</DialogTitle>
          <DialogDescription>
            Import test cases from a CSV or JSON file.
          </DialogDescription>
        </DialogHeader>

        {/* Drop zone */}
        <div
          className={`relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
            dragOver
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          }`}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click()
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.json"
            className="hidden"
            onChange={handleInputChange}
          />
          <FileUp className="h-8 w-8 text-muted-foreground mb-2" />
          {file ? (
            <p className="text-sm font-medium">{file.name}</p>
          ) : (
            <>
              <p className="text-sm font-medium">
                Click to browse or drag and drop
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                .csv or .json files only
              </p>
            </>
          )}
        </div>

        {/* Format hint */}
        <div className="rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground font-mono">
          <p>CSV format: question,expected_answer,category</p>
          <p>JSON format: {'[{"question":"...","expected_answer":"...","category":"..."}]'}</p>
          <p className="mt-1">Category defaults to &quot;general&quot; if omitted.</p>
        </div>

        {/* Upload button */}
        {file && !result && (
          <Button onClick={handleUpload} disabled={uploading} className="w-full">
            <Upload className="h-4 w-4 mr-2" />
            {uploading ? 'Uploading…' : 'Upload'}
          </Button>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-start gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Success result */}
        {result && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-green-700">
              <CheckCircle className="h-4 w-4" />
              <span>
                Imported {result.imported} cases
                {result.skipped > 0 && `, skipped ${result.skipped} rows`}
              </span>
            </div>

            {result.errors.length > 0 && (
              <div>
                <button
                  className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
                  onClick={() => setShowErrors(!showErrors)}
                >
                  {showErrors ? (
                    <ChevronUp className="h-3 w-3" />
                  ) : (
                    <ChevronDown className="h-3 w-3" />
                  )}
                  {result.errors.length} error{result.errors.length > 1 ? 's' : ''}
                </button>
                {showErrors && (
                  <ul className="mt-1 space-y-1 text-xs text-destructive max-h-32 overflow-y-auto">
                    {result.errors.map((err, i) => (
                      <li key={i} className="pl-4">• {err}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            <Button
              variant="secondary"
              className="w-full"
              onClick={() => handleOpenChange(false)}
            >
              Done
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
