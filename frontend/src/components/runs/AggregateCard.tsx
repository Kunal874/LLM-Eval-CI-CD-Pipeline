"use client"

import React from "react"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { RunAggregate } from "@/types"
import {
  CheckCircle2,
  XCircle,
  Activity,
  DollarSign,
  BarChart3,
  Shield,
  Clock,
  AlertTriangle,
} from "lucide-react"

// TODO: Thresholds are not stored in the DB — display without threshold comparison for now.
// Threshold comparison is a future enhancement. When implemented, accept thresholds as props
// and compare metric values against them to determine pass/fail styling.

interface AggregateCardProps {
  aggregates: RunAggregate
}

interface MetricCardProps {
  label: string
  value: string
  icon: React.ReactNode
  status: "pass" | "fail" | "neutral"
}

function MetricCard({ label, value, icon, status }: MetricCardProps) {
  return (
    <Card
      className={cn(
        "transition-all duration-200",
        status === "pass" && "border-green-200 bg-green-50/50",
        status === "fail" && "border-red-200 bg-red-50/50",
        status === "neutral" && "border-gray-200"
      )}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            {label}
          </span>
          <span
            className={cn(
              "flex-shrink-0",
              status === "pass" && "text-green-600",
              status === "fail" && "text-red-500",
              status === "neutral" && "text-gray-400"
            )}
          >
            {icon}
          </span>
        </div>
        <div
          className={cn(
            "text-2xl font-bold tabular-nums",
            status === "pass" && "text-green-700",
            status === "fail" && "text-red-600",
            status === "neutral" && "text-foreground"
          )}
        >
          {value}
        </div>
      </CardContent>
    </Card>
  )
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

function formatMs(value: number): string {
  return `${value.toLocaleString()}ms`
}

function formatCost(value: number): string {
  return `$${value.toFixed(3)}`
}

export function AggregateCards({ aggregates }: AggregateCardProps) {
  const {
    relevancy_avg,
    faithfulness_avg,
    p95_latency_ms,
    hallucination_rate,
    total_cases,
    passed_cases,
    failed_cases,
    overall_passed,
    avg_cost_usd,
    total_cost_usd,
  } = aggregates

  // Determine statuses based on overall_passed and individual values
  // Without thresholds, we use sensible defaults for coloring
  const relevancyStatus = relevancy_avg >= 0.7 ? "pass" : "fail"
  const faithfulnessStatus =
    faithfulness_avg !== null
      ? faithfulness_avg >= 0.7
        ? "pass"
        : "fail"
      : "neutral"
  const latencyStatus = "neutral" as const
  const hallucinationStatus =
    hallucination_rate !== null
      ? hallucination_rate <= 0.1
        ? "pass"
        : "fail"
      : "neutral"

  return (
    <div className="space-y-4">
      {/* Primary metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          label="Relevancy Avg"
          value={formatPercent(relevancy_avg)}
          icon={
            relevancyStatus === "pass" ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )
          }
          status={relevancyStatus}
        />

        {faithfulness_avg !== null && (
          <MetricCard
            label="Faithfulness"
            value={formatPercent(faithfulness_avg)}
            icon={
              faithfulnessStatus === "pass" ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : faithfulnessStatus === "fail" ? (
                <XCircle className="h-4 w-4" />
              ) : (
                <Shield className="h-4 w-4" />
              )
            }
            status={faithfulnessStatus}
          />
        )}

        <MetricCard
          label="p95 Latency"
          value={formatMs(p95_latency_ms)}
          icon={<Clock className="h-4 w-4" />}
          status={latencyStatus}
        />

        {hallucination_rate !== null && (
          <MetricCard
            label="Hallucination"
            value={formatPercent(hallucination_rate)}
            icon={
              hallucinationStatus === "pass" ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <AlertTriangle className="h-4 w-4" />
              )
            }
            status={hallucinationStatus}
          />
        )}
      </div>

      {/* Summary bar */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">Total Cases:</span>
              <span className="font-semibold">{total_cases}</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <span className="text-muted-foreground">Passed:</span>
              <span className="font-semibold text-green-700">{passed_cases}</span>
            </div>
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-500" />
              <span className="text-muted-foreground">Failed:</span>
              <span className="font-semibold text-red-600">{failed_cases}</span>
            </div>
            {avg_cost_usd !== null && (
              <div className="flex items-center gap-2">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Avg Cost:</span>
                <span className="font-semibold">
                  {formatCost(avg_cost_usd)}/query
                </span>
              </div>
            )}
            {total_cost_usd !== null && (
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Total:</span>
                <span className="font-semibold">
                  {formatCost(total_cost_usd)} this run
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
