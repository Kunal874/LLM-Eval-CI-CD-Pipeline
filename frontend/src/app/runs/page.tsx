"use client"

import React, { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { runsApi } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import {
  CheckCircle2,
  XCircle,
  Loader2,
  FlaskConical,
  Terminal,
  GitBranch,
} from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import type { EvalRun } from "@/types"

export default function RunsPage() {
  const router = useRouter()
  const [runs, setRuns] = useState<EvalRun[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    runsApi
      .list({ limit: 50 })
      .then((res) => {
        setRuns(res.data.runs)
        setTotal(res.data.total)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin mb-3" />
        <p className="text-sm">Loading runs…</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Eval Runs</h1>
          <Badge variant="secondary" className="font-mono text-xs">
            {total} runs
          </Badge>
        </div>
      </div>

      {/* Table or empty state */}
      {runs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-center text-muted-foreground">
          <div className="rounded-full bg-muted p-4 mb-4">
            <FlaskConical className="h-8 w-8" />
          </div>
          <p className="text-sm font-medium mb-1">No runs yet.</p>
          <p className="text-xs">
            Run{" "}
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs">
              llmeval run
            </code>{" "}
            in your terminal.
          </p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[60px]">Status</TableHead>
              <TableHead className="w-[140px]">Run ID</TableHead>
              <TableHead className="w-[100px]">Commit</TableHead>
              <TableHead className="w-[140px]">Branch</TableHead>
              <TableHead className="w-[80px]">Cases</TableHead>
              <TableHead className="w-[160px]">Time</TableHead>
              <TableHead className="w-[80px]">Triggered</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {runs.map((run) => (
              <TableRow
                key={run.id}
                className="cursor-pointer"
                onClick={() => router.push(`/runs/${run.id}`)}
              >
                {/* Status */}
                <TableCell>
                  {run.status === "running" ? (
                    <Loader2 className="h-4 w-4 animate-spin text-amber-500" />
                  ) : run.overall_passed ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-500" />
                  )}
                </TableCell>

                {/* Run ID (first 8 chars) */}
                <TableCell className="font-mono text-xs">
                  {run.id.slice(0, 8)}
                </TableCell>

                {/* Commit */}
                <TableCell
                  className={cn(
                    "font-mono text-xs",
                    !run.commit_hash && "text-gray-400"
                  )}
                >
                  {run.commit_hash ? run.commit_hash.slice(0, 7) : "—"}
                </TableCell>

                {/* Branch */}
                <TableCell className="max-w-[140px] truncate">
                  <div className="flex items-center gap-1.5">
                    {run.branch && (
                      <GitBranch className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                    )}
                    <span className="truncate text-xs">
                      {run.branch || "—"}
                    </span>
                  </div>
                </TableCell>

                {/* Cases — only show if completed/failed and overall_passed is defined */}
                <TableCell className="text-xs">
                  {run.status === "running" ? (
                    <span className="text-muted-foreground">…</span>
                  ) : (
                    "—"
                  )}
                </TableCell>

                {/* Time */}
                <TableCell className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(run.created_at), {
                    addSuffix: true,
                  })}
                </TableCell>

                {/* Triggered */}
                <TableCell>
                  <Badge
                    variant="outline"
                    className="text-[10px] px-1.5 py-0"
                  >
                    {run.triggered_by === "github_actions" ? (
                      <span className="flex items-center gap-1">CI</span>
                    ) : (
                      <span className="flex items-center gap-1">
                        <Terminal className="h-2.5 w-2.5" />
                        CLI
                      </span>
                    )}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
