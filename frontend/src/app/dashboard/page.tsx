"use client"

import React, { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { runsApi } from "@/lib/api"
import { MetricChart } from "@/components/dashboard/MetricChart"
import { RunsTimeline } from "@/components/dashboard/RunsTimeline"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { BarChart2, Loader2, ArrowRight } from "lucide-react"
import type { RunMetric } from "@/types"

export default function DashboardPage() {
  const router = useRouter()
  const [runs, setRuns] = useState<RunMetric[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    runsApi
      .getMetrics(20)
      .then((res) => {
        setRuns(res.data.runs)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin mb-3" />
        <p className="text-sm">Loading trend data…</p>
      </div>
    )
  }

  if (runs.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold">Trend Dashboard</h1>
          <p className="text-sm text-muted-foreground">Last 20 completed runs</p>
        </div>

        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="rounded-full bg-muted p-4 mb-4">
              <BarChart2 className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="text-base font-semibold mb-1">No completed runs yet</h3>
            <p className="text-sm text-muted-foreground max-w-sm mb-6">
              Run <code className="bg-muted px-1.5 py-0.5 rounded font-mono text-xs">llmeval run</code> locally or push a commit with the GitHub Action configured.
            </p>
            <Button size="sm" onClick={() => router.push("/runs")}>
              Go to Runs
              <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold">Trend Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Last {runs.length} completed run{runs.length === 1 ? "" : "s"}
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <MetricChart
          title="Answer Relevancy"
          data={runs}
          metricKey="relevancy_avg"
          formatter={(v) => `${(v * 100).toFixed(1)}%`}
          color="#3b82f6"
        />
        <MetricChart
          title="Faithfulness"
          data={runs}
          metricKey="faithfulness_avg"
          formatter={(v) => `${(v * 100).toFixed(1)}%`}
          color="#10b981"
        />
        <MetricChart
          title="p95 Latency"
          data={runs}
          metricKey="p95_latency_ms"
          formatter={(v) => `${v.toLocaleString()}ms`}
          color="#f59e0b"
        />
        <MetricChart
          title="Hallucination Rate"
          data={runs}
          metricKey="hallucination_rate"
          formatter={(v) => `${(v * 100).toFixed(1)}%`}
          invertPass={true}
          color="#ef4444"
        />
      </div>

      {/* Runs Timeline Table */}
      <RunsTimeline runs={runs} />
    </div>
  )
}
