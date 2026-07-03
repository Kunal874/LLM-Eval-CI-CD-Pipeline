import { BarChart2 } from 'lucide-react'

export default function DashboardPage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="rounded-full bg-muted p-4 mb-4">
        <BarChart2 className="h-8 w-8 text-muted-foreground" />
      </div>
      <h1 className="text-2xl font-semibold mb-2">Dashboard</h1>
      <p className="text-muted-foreground">Coming in Phase 3C.</p>
    </div>
  )
}
