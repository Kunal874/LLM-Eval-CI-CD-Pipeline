import type { Metadata } from "next"
import "./globals.css"
import { ClientLayout } from "./client-layout"

export const metadata: Metadata = {
  title: "llmeval — LLM Evaluation Dashboard",
  description: "CI/CD evaluation framework for LLM-powered applications. Manage test datasets, run evaluations, and track quality metrics.",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  )
}
