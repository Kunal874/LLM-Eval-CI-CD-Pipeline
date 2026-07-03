'use client'

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { Plus, Upload, Download, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
  TableCell,
} from '@/components/ui/table'
import { DatasetTable } from '@/components/dataset/DatasetTable'
import { UploadDialog } from '@/components/dataset/UploadDialog'
import { casesApi } from '@/lib/api'
import type { TestCase } from '@/types'

export default function DatasetPage() {
  const [cases, setCases] = useState<TestCase[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)

  // Add-case inline form state
  const [newQuestion, setNewQuestion] = useState('')
  const [newExpectedAnswer, setNewExpectedAnswer] = useState('')
  const [newCategory, setNewCategory] = useState('')
  const [addingSaving, setAddingSaving] = useState(false)

  const fetchCases = useCallback(async () => {
    setLoading(true)
    try {
      const res = await casesApi.list({ limit: 1000 })
      setCases(res.data.cases)
      setTotal(res.data.total)
    } catch (err) {
      console.error('Failed to fetch cases:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchCases()
  }, [fetchCases])

  // Unique categories from data
  const categories = useMemo(() => {
    const cats = new Set(cases.map((c) => c.category))
    return Array.from(cats).sort()
  }, [cases])

  // Filter cases by selected category (client-side)
  const filteredCases = useMemo(() => {
    if (!selectedCategory) return cases
    return cases.filter((c) => c.category === selectedCategory)
  }, [cases, selectedCategory])

  // Handlers
  const handleSave = useCallback(
    async (
      id: string,
      data: { question: string; expected_answer: string; category: string }
    ) => {
      const res = await casesApi.update(id, data)
      setCases((prev) =>
        prev.map((c) => (c.id === id ? res.data : c))
      )
      setEditingId(null)
    },
    []
  )

  const handleDelete = useCallback(async (id: string) => {
    try {
      await casesApi.delete(id)
      setCases((prev) => prev.filter((c) => c.id !== id))
      setTotal((prev) => prev - 1)
    } catch (err) {
      console.error('Failed to delete case:', err)
    }
  }, [])

  const handleAddCase = useCallback(async () => {
    if (!newQuestion.trim() || !newExpectedAnswer.trim()) return
    setAddingSaving(true)
    try {
      const res = await casesApi.create({
        question: newQuestion.trim(),
        expected_answer: newExpectedAnswer.trim(),
        category: newCategory.trim() || undefined,
      })
      setCases((prev) => [res.data, ...prev])
      setTotal((prev) => prev + 1)
      setNewQuestion('')
      setNewExpectedAnswer('')
      setNewCategory('')
      setShowAddForm(false)
    } catch (err) {
      console.error('Failed to add case:', err)
    } finally {
      setAddingSaving(false)
    }
  }, [newQuestion, newExpectedAnswer, newCategory])

  const handleExportYaml = useCallback(async () => {
    try {
      const res = await casesApi.exportYaml()
      const blob = new Blob([res.data], { type: 'application/x-yaml' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'dataset.yml'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to export YAML:', err)
    }
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Dataset Manager</h1>
          <Badge variant="secondary" className="text-sm">
            {total} test case{total !== 1 ? 's' : ''}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowUploadDialog(true)}
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload CSV/JSON
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setShowAddForm(true)
              setEditingId(null)
            }}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Case
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportYaml}>
            <Download className="h-4 w-4 mr-2" />
            Export YAML
          </Button>
        </div>
      </div>

      {/* Category filter */}
      {categories.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <button
            className={`px-3 py-1 rounded-full text-sm transition-colors ${
              selectedCategory === null
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
            }`}
            onClick={() => setSelectedCategory(null)}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                selectedCategory === cat
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
              onClick={() =>
                setSelectedCategory(selectedCategory === cat ? null : cat)
              }
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          {/* Inline add form */}
          {showAddForm && (
            <div className="rounded-lg border bg-card p-4 space-y-3">
              <h3 className="text-sm font-medium">Add New Test Case</h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[40px]">#</TableHead>
                    <TableHead>Question</TableHead>
                    <TableHead>Expected Answer</TableHead>
                    <TableHead className="w-[120px]">Category</TableHead>
                    <TableHead className="w-[80px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="w-[40px] text-muted-foreground">
                      —
                    </TableCell>
                    <TableCell>
                      <textarea
                        value={newQuestion}
                        onChange={(e) => setNewQuestion(e.target.value)}
                        placeholder="Enter question…"
                        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none min-h-[60px]"
                        rows={2}
                      />
                    </TableCell>
                    <TableCell>
                      <textarea
                        value={newExpectedAnswer}
                        onChange={(e) => setNewExpectedAnswer(e.target.value)}
                        placeholder="Enter expected answer…"
                        className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none min-h-[60px]"
                        rows={2}
                      />
                    </TableCell>
                    <TableCell className="w-[120px]">
                      <input
                        type="text"
                        value={newCategory}
                        onChange={(e) => setNewCategory(e.target.value)}
                        placeholder="general"
                        className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      />
                    </TableCell>
                    <TableCell className="w-[80px]">
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-green-600 hover:text-green-700 hover:bg-green-50"
                          onClick={handleAddCase}
                          disabled={
                            addingSaving ||
                            !newQuestion.trim() ||
                            !newExpectedAnswer.trim()
                          }
                        >
                          Save
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setShowAddForm(false)
                            setNewQuestion('')
                            setNewExpectedAnswer('')
                            setNewCategory('')
                          }}
                        >
                          Cancel
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          )}

          {/* Main dataset table */}
          <DatasetTable
            cases={filteredCases}
            editingId={editingId}
            onEdit={(id) => {
              setEditingId(id)
              setShowAddForm(false)
            }}
            onCancelEdit={() => setEditingId(null)}
            onSave={handleSave}
            onDelete={handleDelete}
          />
        </>
      )}

      {/* Upload dialog */}
      <UploadDialog
        open={showUploadDialog}
        onOpenChange={setShowUploadDialog}
        onUploadComplete={fetchCases}
      />
    </div>
  )
}
