"use client"

import React from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from "recharts"
import type { RunMetric } from "@/types"

interface MetricChartProps {
  title: string
  data: RunMetric[]
  metricKey: keyof RunMetric
  formatter: (value: number) => string
  threshold?: number
  thresholdLabel?: string
  invertPass?: boolean
  color?: string
}

export function MetricChart({
  title,
  data,
  metricKey,
  formatter,
  threshold,
  thresholdLabel,
  color = "#3b82f6",
}: MetricChartProps) {
  const filtered = data.filter(
    (run) => run[metricKey] !== null && run[metricKey] !== undefined
  )

  const chartData = [...filtered].reverse().map((run, i) => ({
    x: i + 1,
    value: Number(run[metricKey]),
    commit: run.commit_hash?.slice(0, 7) ?? "no-commit",
    branch: run.branch ?? "",
  }))

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold">{title}</CardTitle>
        </CardHeader>
        <CardContent className="h-[200px] flex items-center justify-center text-center p-6">
          <p className="text-sm text-muted-foreground">
            {title === "Faithfulness" || title === "Hallucination Rate"
              ? `${title} is only tracked for RAG pipelines.`
              : "No data available."}
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 10, right: 15, left: 10, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
              <XAxis
                dataKey="x"
                tickLine={false}
                axisLine={false}
                fontSize={12}
                stroke="#6b7280"
                tickFormatter={(val) => `#${val}`}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                fontSize={12}
                stroke="#6b7280"
                tickFormatter={(val) => formatter(Number(val))}
                domain={["auto", "auto"]}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const pt = payload[0].payload
                    return (
                      <div className="rounded-lg border bg-background p-2.5 shadow-md text-xs space-y-1">
                        <div className="font-bold text-foreground">
                          {formatter(pt.value)}
                        </div>
                        <div className="text-muted-foreground font-mono">
                          commit: {pt.commit}
                        </div>
                        {pt.branch && (
                          <div className="text-muted-foreground">
                            branch: {pt.branch}
                          </div>
                        )}
                      </div>
                    )
                  }
                  return null
                }}
              />
              {threshold !== undefined && (
                <ReferenceLine
                  y={threshold}
                  stroke="#ef4444"
                  strokeDasharray="4 4"
                  label={{
                    value: thresholdLabel || `min ${formatter(threshold)}`,
                    fill: "#ef4444",
                    fontSize: 10,
                    position: "right",
                  }}
                />
              )}
              <Line
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                dot={{ r: 4, fill: color }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
