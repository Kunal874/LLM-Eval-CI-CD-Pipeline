'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Check, X, Pencil, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { TableRow, TableCell } from '@/components/ui/table'
import type { TestCase } from '@/types'

interface CaseRowProps {
  testCase: TestCase
  index: number
  isEditing: boolean
  onEdit: () => void
  onCancelEdit: () => void
  onSave: (id: string, data: { question: string; expected_answer: string; category: string }) => Promise<void>
  onDelete: (id: string) => void
}

function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text
  return text.slice(0, maxLen) + '…'
}

function AutoResizeTextarea({
  value,
  onChange,
  className,
}: {
  value: string
  onChange: (val: string) => void
  className?: string
}) {
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = 'auto'
      ref.current.style.height = ref.current.scrollHeight + 'px'
    }
  }, [value])

  return (
    <textarea
      ref={ref}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none overflow-hidden ${className ?? ''}`}
      rows={1}
    />
  )
}

export function CaseRow({
  testCase,
  index,
  isEditing,
  onEdit,
  onCancelEdit,
  onSave,
  onDelete,
}: CaseRowProps) {
  const [question, setQuestion] = useState(testCase.question)
  const [expectedAnswer, setExpectedAnswer] = useState(testCase.expected_answer)
  const [category, setCategory] = useState(testCase.category)
  const [saving, setSaving] = useState(false)

  // Reset edit values when entering edit mode
  useEffect(() => {
    if (isEditing) {
      setQuestion(testCase.question)
      setExpectedAnswer(testCase.expected_answer)
      setCategory(testCase.category)
    }
  }, [isEditing, testCase])

  const handleSave = useCallback(async () => {
    setSaving(true)
    try {
      await onSave(testCase.id, { question, expected_answer: expectedAnswer, category })
    } finally {
      setSaving(false)
    }
  }, [testCase.id, question, expectedAnswer, category, onSave])

  const handleDelete = useCallback(() => {
    if (window.confirm(`Delete this test case?\n\n"${truncate(testCase.question, 80)}"`)) {
      onDelete(testCase.id)
    }
  }, [testCase.id, testCase.question, onDelete])

  if (isEditing) {
    return (
      <TableRow>
        <TableCell className="w-[40px] text-muted-foreground">{index}</TableCell>
        <TableCell>
          <AutoResizeTextarea value={question} onChange={setQuestion} />
        </TableCell>
        <TableCell>
          <AutoResizeTextarea value={expectedAnswer} onChange={setExpectedAnswer} />
        </TableCell>
        <TableCell className="w-[120px]">
          <input
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          />
        </TableCell>
        <TableCell className="w-[80px]">
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-green-600 hover:text-green-700 hover:bg-green-50"
              onClick={handleSave}
              disabled={saving}
            >
              <Check className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-gray-500 hover:text-gray-700"
              onClick={onCancelEdit}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </TableCell>
      </TableRow>
    )
  }

  return (
    <TableRow>
      <TableCell className="w-[40px] text-muted-foreground">{index}</TableCell>
      <TableCell title={testCase.question}>{truncate(testCase.question, 60)}</TableCell>
      <TableCell title={testCase.expected_answer}>{truncate(testCase.expected_answer, 60)}</TableCell>
      <TableCell className="w-[120px]">
        <Badge variant="secondary">{testCase.category}</Badge>
      </TableCell>
      <TableCell className="w-[80px]">
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-gray-500 hover:text-gray-700"
            onClick={onEdit}
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-gray-500 hover:text-red-600 hover:bg-red-50"
            onClick={handleDelete}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </TableCell>
    </TableRow>
  )
}
