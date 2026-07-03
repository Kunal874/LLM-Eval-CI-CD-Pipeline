"use client"

import React, { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { runsApi } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AggregateCards } from "@/components/runs/AggregateCard"
import { RunResultsTable } from "@/components/runs/RunResultsTable"
import { cn } from "@/lib/utils"
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  XCircle,
  GitCommit,
  GitBranch,
  Terminal,
  AlertTriangle,
} from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import type { EvalRun, RunAggregate, CaseResult } from "@/types"

export default function RunDetailPage() {
  const params = useParams()
  const router = useRouter()
  const runId = params.runId as string

  const [run, setRun] = useState<EvalRun | null>(null)
  const [aggregates, setAggregates] = useState<RunAggregate | null>(null)
  const [results, setResults] = useState<CaseResult[]>([])
  const [loading, setLoading] = useState(true)
  const [resultsLoading, setResultsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!runId) return

    // Fetch run metadata + aggregates
    runsApi
      .get(runId)
      .then((res) => {
        setRun(res.data.run)
        setAggregates(res.data.aggregates)
      })
      .catch((err) => {
        if (err.response?.status === 404) {
          setError("not_found")
        } else {
          setError("error")
        }
      })
      .finally(() => setLoading(false))

    // Fetch results
    runsApi
      .getResults(runId, { limit: 500 })
      .then((res) => {
        setResults(res.data.results)
      })
      .catch(() => {
        // Results may not be available yet if run is in progress
      })
      .finally(() => setResultsLoading(false))
  }, [runId])

  // Loading state
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin mb-3" />
        <p className="text-sm">Loading run details…</p>
      </div>
    )
  }

  // 404 state
  if (error === "not_found" || !run) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="rounded-full bg-muted p-4 mb-4">
          <AlertTriangle className="h-8 w-8 text-muted-foreground" />
        </div>
        <h1 className="text-xl font-semibold mb-2">Run not found</h1>
        <p className="text-sm text-muted-foreground mb-6">
          Run ID <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono">{runId}</code> does
          not exist.
        </p>
        <Button variant="outline" size="sm" onClick={() => router.push("/runs")}>
          <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
          Back to Runs
        </Button>
      </div>
    )
  }

  // Error state
  if (error === "error") {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="rounded-full bg-red-50 p-4 mb-4">
          <XCircle className="h-8 w-8 text-red-500" />
        </div>
        <h1 className="text-xl font-semibold mb-2">Failed to load run</h1>
        <p className="text-sm text-muted-foreground mb-6">
          There was an error loading this run. Check that the backend is running.
        </p>
        <Button variant="outline" size="sm" onClick={() => router.push("/runs")}>
          <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
          Back to Runs
        </Button>
      </div>
    )
  }

  const shortId = run.id.slice(0, 8)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-3">
        {/* Back link + title */}
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2"
            onClick={() => router.push("/runs")}
          >
            <ArrowLeft className="h-3.5 w-3.5 mr-1" />
            Runs
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-semibold font-mono">
            Run {shortId}
          </h1>

          {/* Status badge */}
          <Badge
            className={cn(
              "text-xs font-semibold",
              run.status === "completed" &&
                run.overall_passed !== false &&
                "bg-green-100 text-green-800 border-green-200",
              run.status === "completed" &&
                run.overall_passed === false &&
                "bg-red-100 text-red-800 border-red-200",
              run.status === "failed" &&
                "bg-red-100 text-red-800 border-red-200",
              run.status === "running" &&
                "bg-amber-100 text-amber-800 border-amber-200"
            )}
            variant="outline"
          >
            {run.status === "running" && (
              <Loader2 className="h-3 w-3 animate-spin mr-1" />
            )}
            {run.status === "completed" && run.overall_passed !== false && (
              <CheckCircle2 className="h-3 w-3 mr-1" />
            )}
            {(run.status === "failed" ||
              (run.status === "completed" && run.overall_passed === false)) && (
              <XCircle className="h-3 w-3 mr-1" />
            )}
            {run.status === "completed"
              ? run.overall_passed !== false
                ? "PASSED"
                : "FAILED"
              : run.status.toUpperCase()}
          </Badge>
        </div>

        {/* Metadata line */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
          {run.commit_hash && (
            <span className="flex items-center gap-1">
              <GitCommit className="h-3 w-3" />
              <span className="font-mono">{run.commit_hash.slice(0, 7)}</span>
            </span>
          )}
          {run.branch && (
            <span className="flex items-center gap-1">
              <GitBranch className="h-3 w-3" />
              {run.branch}
            </span>
          )}
          <span>
            {formatDistanceToNow(new Date(run.created_at), {
              addSuffix: true,
            })}
          </span>
          <Badge variant="outline" className="text-[10px] px-1.5 py-0">
            {run.triggered_by === "github_actions" ? (
              "via GitHub Actions"
            ) : (
              <span className="flex items-center gap-1">
                <Terminal className="h-2.5 w-2.5" />
                via CLI
              </span>
            )}
          </Badge>
        </div>
      </div>

      {/* Aggregate cards */}
      {aggregates && <AggregateCards aggregates={aggregates} />}

      {/* Results table */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Case Results</h2>
        <RunResultsTable results={results} loading={resultsLoading} />
      </div>
    </div>
  )
}
