"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { DatabaseZap, FlaskConical, BarChart2 } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { label: "Dataset", href: "/dataset", icon: DatabaseZap },
  { label: "Runs", href: "/runs", icon: FlaskConical },
  { label: "Dashboard", href: "/dashboard", icon: BarChart2 },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed inset-y-0 left-0 z-30 w-[220px] border-r bg-background flex flex-col">
      <div className="flex h-14 items-center px-5 border-b">
        <span className="font-mono text-lg font-bold text-primary">
          llmeval
        </span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-600 font-medium"
                  : "text-gray-600 hover:bg-gray-50"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
