"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { ChevronRight } from "lucide-react"
import { TableRow, TableCell } from "@/components/ui/table"
import type { CaseResult } from "@/types"

interface CaseResultRowProps {
  result: CaseResult
  expanded: boolean
  onToggle: () => void
}

function scoreColor(score: number | null): string {
  if (score === null) return "text-gray-400"
  if (score >= 0.9) return "text-green-600"
  if (score >= 0.7) return "text-amber-500"
  return "text-red-500"
}

function formatScore(score: number | null): string {
  if (score === null) return "N/A"
  return `${(score * 100).toFixed(1)}%`
}

export function CaseResultRow({ result, expanded, onToggle }: CaseResultRowProps) {
  return (
    <>
      <TableRow
        className="cursor-pointer select-none"
        onClick={onToggle}
      >
        {/* Status */}
        <TableCell className="w-[40px]">
          <div
            className={cn(
              "h-2.5 w-2.5 rounded-full",
              result.passed ? "bg-green-500" : "bg-red-500"
            )}
          />
        </TableCell>

        {/* Question */}
        <TableCell
          className="max-w-0 w-[30%] truncate"
          title={result.question}
        >
          {result.question}
        </TableCell>

        {/* Expected */}
        <TableCell
          className="max-w-0 w-[20%] truncate"
          title={result.expected_answer}
        >
          {result.expected_answer}
        </TableCell>

        {/* Actual */}
        <TableCell
          className={cn(
            "max-w-0 w-[20%] truncate",
            result.error && "text-red-500"
          )}
          title={result.error || result.actual_answer || ""}
        >
          {result.error ? (
            <span className="italic">{result.error}</span>
          ) : (
            result.actual_answer || "—"
          )}
        </TableCell>

        {/* Relevancy */}
        <TableCell className={cn("w-[80px] font-mono tabular-nums", scoreColor(result.relevancy_score))}>
          {formatScore(result.relevancy_score)}
        </TableCell>

        {/* Faithfulness */}
        <TableCell className={cn("w-[80px] font-mono tabular-nums", scoreColor(result.faithfulness_score))}>
          {formatScore(result.faithfulness_score)}
        </TableCell>

        {/* Latency */}
        <TableCell className="w-[80px] font-mono tabular-nums">
          {result.latency_ms.toLocaleString()}ms
        </TableCell>

        {/* Expand toggle */}
        <TableCell className="w-[40px]">
          <ChevronRight
            className={cn(
              "h-4 w-4 text-muted-foreground transition-transform duration-200",
              expanded && "rotate-90"
            )}
          />
        </TableCell>
      </TableRow>

      {/* Expanded detail view */}
      {expanded && (
        <TableRow className="bg-muted/30 hover:bg-muted/30">
          <TableCell colSpan={8} className="p-0">
            <div className="px-6 py-4 space-y-4 border-l-4 border-primary/20">
              {/* Question */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Question
                </h4>
                <p className="text-sm whitespace-pre-wrap">{result.question}</p>
              </div>

              {/* Expected */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Expected Answer
                </h4>
                <p className="text-sm whitespace-pre-wrap">{result.expected_answer}</p>
              </div>

              {/* Actual */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Actual Answer
                </h4>
                {result.error ? (
                  <p className="text-sm text-red-500 whitespace-pre-wrap font-medium">
                    Error: {result.error}
                  </p>
                ) : (
                  <p className="text-sm whitespace-pre-wrap">
                    {result.actual_answer || "—"}
                  </p>
                )}
              </div>

              {/* Context — placeholder for RAG pipeline results */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Context
                </h4>
                <p className="text-sm text-muted-foreground italic">
                  No context (non-RAG pipeline)
                </p>
              </div>

              {/* Scores */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                  Scores
                </h4>
                <div className="flex gap-6 text-sm">
                  <span>
                    <span className="text-muted-foreground">faithfulness: </span>
                    <span className={cn("font-mono font-medium", scoreColor(result.faithfulness_score))}>
                      {result.faithfulness_score !== null
                        ? result.faithfulness_score.toFixed(3)
                        : "N/A"}
                    </span>
                  </span>
                  <span>
                    <span className="text-muted-foreground">relevancy: </span>
                    <span className={cn("font-mono font-medium", scoreColor(result.relevancy_score))}>
                      {result.relevancy_score !== null
                        ? result.relevancy_score.toFixed(3)
                        : "N/A"}
                    </span>
                  </span>
                  <span>
                    <span className="text-muted-foreground">latency: </span>
                    <span className="font-mono font-medium">
                      {result.latency_ms.toLocaleString()}ms
                    </span>
                  </span>
                  {result.cost_usd !== null && (
                    <span>
                      <span className="text-muted-foreground">cost: </span>
                      <span className="font-mono font-medium">
                        ${result.cost_usd.toFixed(4)}
                      </span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  )
}
