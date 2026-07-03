"use client"

import React from "react"
import { Sidebar } from "@/components/Sidebar"

export function ClientLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <main className="ml-[220px] p-8">{children}</main>
    </div>
  )
}
