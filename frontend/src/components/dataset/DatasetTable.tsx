'use client'

import React from 'react'
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { CaseRow } from './CaseRow'
import type { TestCase } from '@/types'

interface DatasetTableProps {
  cases: TestCase[]
  editingId: string | null
  onEdit: (id: string) => void
  onCancelEdit: () => void
  onSave: (id: string, data: { question: string; expected_answer: string; category: string }) => Promise<void>
  onDelete: (id: string) => void
}

export function DatasetTable({
  cases,
  editingId,
  onEdit,
  onCancelEdit,
  onSave,
  onDelete,
}: DatasetTableProps) {
  if (cases.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="rounded-full bg-muted p-4 mb-4">
          <svg
            className="h-8 w-8 text-muted-foreground"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
            />
          </svg>
        </div>
        <p className="text-muted-foreground">
          No test cases yet. Upload a CSV or add one manually.
        </p>
      </div>
    )
  }

  return (
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
        {cases.map((tc, i) => (
          <CaseRow
            key={tc.id}
            testCase={tc}
            index={i + 1}
            isEditing={editingId === tc.id}
            onEdit={() => onEdit(tc.id)}
            onCancelEdit={onCancelEdit}
            onSave={onSave}
            onDelete={onDelete}
          />
        ))}
      </TableBody>
    </Table>
  )
}
