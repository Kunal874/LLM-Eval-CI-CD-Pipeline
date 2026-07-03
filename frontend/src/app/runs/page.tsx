import { FlaskConical } from 'lucide-react'

export default function RunsPage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="rounded-full bg-muted p-4 mb-4">
        <FlaskConical className="h-8 w-8 text-muted-foreground" />
      </div>
      <h1 className="text-2xl font-semibold mb-2">Eval Runs</h1>
      <p className="text-muted-foreground">Coming in Phase 3B.</p>
    </div>
  )
}
