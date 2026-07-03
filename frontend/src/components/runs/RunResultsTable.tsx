"use client"

import React, { useState, useMemo } from "react"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table"
import { CaseResultRow } from "@/components/runs/CaseResultRow"
import { cn } from "@/lib/utils"
import { Search, Loader2, Inbox, CheckCircle2 } from "lucide-react"
import type { CaseResult } from "@/types"

type SortOption =
  | "default"
  | "worst_relevancy"
  | "worst_faithfulness"
  | "slowest"

interface RunResultsTableProps {
  results: CaseResult[]
  loading: boolean
}

export function RunResultsTable({ results, loading }: RunResultsTableProps) {
  const [failedOnly, setFailedOnly] = useState(false)
  const [sortBy, setSortBy] = useState<SortOption>("default")
  const [searchQuery, setSearchQuery] = useState("")
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const filteredAndSorted = useMemo(() => {
    let filtered = results

    // Filter: failed only
    if (failedOnly) {
      filtered = filtered.filter((r) => !r.passed)
    }

    // Filter: search
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      filtered = filtered.filter((r) => r.question.toLowerCase().includes(q))
    }

    // Sort
    const sorted = [...filtered]
    switch (sortBy) {
      case "worst_relevancy":
        sorted.sort((a, b) => (a.relevancy_score ?? 1) - (b.relevancy_score ?? 1))
        break
      case "worst_faithfulness":
        sorted.sort(
          (a, b) => (a.faithfulness_score ?? 1) - (b.faithfulness_score ?? 1)
        )
        break
      case "slowest":
        sorted.sort((a, b) => b.latency_ms - a.latency_ms)
        break
      default:
        break
    }

    return sorted
  }, [results, failedOnly, sortBy, searchQuery])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin mb-3" />
        <p className="text-sm">Loading results…</p>
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <Inbox className="h-10 w-10 mb-3" />
        <p className="text-sm font-medium">This run has no results yet.</p>
        <p className="text-xs">It may still be running.</p>
      </div>
    )
  }

  const failedCount = results.filter((r) => !r.passed).length

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        {/* All / Failed only toggle */}
        <div className="inline-flex rounded-md border overflow-hidden">
          <button
            onClick={() => setFailedOnly(false)}
            className={cn(
              "px-3 py-1.5 text-xs font-medium transition-colors",
              !failedOnly
                ? "bg-primary text-primary-foreground"
                : "bg-background hover:bg-muted text-muted-foreground"
            )}
          >
            All ({results.length})
          </button>
          <button
            onClick={() => setFailedOnly(true)}
            className={cn(
              "px-3 py-1.5 text-xs font-medium transition-colors border-l",
              failedOnly
                ? "bg-red-500 text-white"
                : "bg-background hover:bg-muted text-muted-foreground"
            )}
          >
            Failed only ({failedCount})
          </button>
        </div>

        {/* Sort dropdown */}
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as SortOption)}
          className="h-8 rounded-md border px-2 text-xs bg-background"
        >
          <option value="default">Default order</option>
          <option value="worst_relevancy">Worst relevancy first</option>
          <option value="worst_faithfulness">Worst faithfulness first</option>
          <option value="slowest">Slowest first</option>
        </select>

        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search questions…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 h-8 text-xs"
          />
        </div>
      </div>

      {/* Results table */}
      {filteredAndSorted.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <CheckCircle2 className="h-8 w-8 mb-3 text-green-500" />
          <p className="text-sm font-medium">
            {failedOnly
              ? "No failed cases — all cases passed."
              : "No results matching filter."}
          </p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40px]">Status</TableHead>
              <TableHead className="w-[30%]">Question</TableHead>
              <TableHead className="w-[20%]">Expected</TableHead>
              <TableHead className="w-[20%]">Actual</TableHead>
              <TableHead className="w-[80px]">Relevancy</TableHead>
              <TableHead className="w-[80px]">Faith.</TableHead>
              <TableHead className="w-[80px]">Latency</TableHead>
              <TableHead className="w-[40px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAndSorted.map((result) => (
              <CaseResultRow
                key={result.id}
                result={result}
                expanded={expandedId === result.id}
                onToggle={() =>
                  setExpandedId(expandedId === result.id ? null : result.id)
                }
              />
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
