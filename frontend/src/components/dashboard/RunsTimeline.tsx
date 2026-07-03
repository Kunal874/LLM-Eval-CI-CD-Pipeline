"use client"

import React from "react"
import { useRouter } from "next/navigation"
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import { formatDistanceToNow } from "date-fns"
import type { RunMetric } from "@/types"

interface RunsTimelineProps {
  runs: RunMetric[]
}

export function RunsTimeline({ runs }: RunsTimelineProps) {
  const router = useRouter()

  if (runs.length === 0) {
    return null
  }

  return (
    <div className="space-y-3">
      <h2 className="text-base font-semibold">Recent Runs</h2>
      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[40px]">Status</TableHead>
              <TableHead className="w-[80px]">Commit</TableHead>
              <TableHead className="max-w-[140px]">Branch</TableHead>
              <TableHead className="w-[80px]">Relevancy</TableHead>
              <TableHead className="w-[80px]">Faith.</TableHead>
              <TableHead className="w-[100px]">p95 Latency</TableHead>
              <TableHead className="w-[120px]">Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {runs.map((run) => (
              <TableRow
                key={run.id}
                className="cursor-pointer"
                onClick={() => router.push(`/runs/${run.id}`)}
              >
                <TableCell>
                  <div
                    className={cn(
                      "h-2.5 w-2.5 rounded-full",
                      run.overall_passed ? "bg-green-500" : "bg-red-500"
                    )}
                  />
                </TableCell>
                <TableCell className="font-mono text-xs">
                  {run.commit_hash ? run.commit_hash.slice(0, 7) : "—"}
                </TableCell>
                <TableCell className="max-w-[140px] truncate text-xs">
                  {run.branch || "—"}
                </TableCell>
                <TableCell className="font-mono text-xs tabular-nums">
                  {(run.relevancy_avg * 100).toFixed(1)}%
                </TableCell>
                <TableCell className="font-mono text-xs tabular-nums">
                  {run.faithfulness_avg !== null
                    ? `${(run.faithfulness_avg * 100).toFixed(1)}%`
                    : "N/A"}
                </TableCell>
                <TableCell className="font-mono text-xs tabular-nums">
                  {run.p95_latency_ms.toLocaleString()}ms
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(run.created_at), {
                    addSuffix: true,
                  })}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
