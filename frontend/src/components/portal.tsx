"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { ReactNode } from 'react'

import { navItems } from '@/lib/site-data'

type PortalShellProps = {
  title: string
  subtitle: string
  badge?: string
  actions?: ReactNode
  children: ReactNode
  aside?: ReactNode
}

export function PortalShell({ title, subtitle, badge, actions, children, aside }: PortalShellProps) {
  const pathname = usePathname()

  return (
    <div className="page-grid min-h-screen text-white">
      <div className="mx-auto grid min-h-screen w-full max-w-[1600px] grid-cols-1 gap-6 px-4 py-4 lg:grid-cols-[280px_minmax(0,1fr)] lg:px-6 lg:py-6">
        <aside className="glass-panel relative overflow-hidden p-5">
          <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-r from-cyan-400/20 via-blue-400/10 to-transparent" />
          <div className="relative">
            <div className="pill mb-5">Studentska Platforma</div>
            <h2 className="text-2xl font-black tracking-tight text-white">Univerzitetske konsultacije</h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">Sve što profesor, student i admin treba da urade na jednom mestu.</p>
          </div>

          <nav className="mt-8 space-y-2">
            {navItems.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block rounded-2xl border px-4 py-3 transition ${active ? 'border-cyan-300/60 bg-cyan-300/10' : 'border-slate-700 bg-slate-950/40 hover:border-slate-500 hover:bg-slate-900/70'}`}
                >
                  <div className="text-sm font-semibold text-white">{item.label}</div>
                  <div className="mt-1 text-xs leading-5 text-slate-400">{item.description}</div>
                </Link>
              )
            })}
          </nav>

          <div className="mt-8 rounded-2xl border border-slate-700/70 bg-slate-950/55 p-4 text-sm text-slate-300">
            <div className="section-title mb-3">Status sistema</div>
            <div className="flex items-center justify-between">
              <span>Backend</span>
              <span className="text-emerald-300">Online</span>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <span>Keycloak</span>
              <span className="text-emerald-300">Ready</span>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <span>Frontend</span>
              <span className="text-cyan-300">MVP UI</span>
            </div>
          </div>
        </aside>

        <section className="space-y-6">
          <header className="glass-panel flex flex-col gap-4 p-5 md:flex-row md:items-end md:justify-between">
            <div>
              {badge ? <div className="pill mb-3">{badge}</div> : null}
              <h1 className="text-3xl font-black tracking-tight text-white md:text-4xl">{title}</h1>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300 md:text-base">{subtitle}</p>
            </div>
            {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
          </header>

          <main className="space-y-6">{children}</main>

          {aside ? <div className="glass-panel p-5">{aside}</div> : null}
        </section>
      </div>
    </div>
  )
}

export function SectionCard({
  title,
  eyebrow,
  description,
  children,
  className = '',
}: {
  title: string
  eyebrow?: string
  description?: string
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`glass-panel p-5 ${className}`}>
      {eyebrow ? <div className="section-title">{eyebrow}</div> : null}
      <div className="mt-1 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">{title}</h2>
          {description ? <p className="mt-1 text-sm leading-6 text-slate-300">{description}</p> : null}
        </div>
      </div>
      <div className="mt-5">{children}</div>
    </section>
  )
}

export function StatCard({ label, value, detail, tone = 'cyan' }: { label: string; value: string; detail: string; tone?: 'cyan' | 'blue' | 'green' | 'red' }) {
  const toneClass =
    tone === 'green'
      ? 'from-emerald-400/25 to-emerald-500/5 border-emerald-400/30'
      : tone === 'red'
        ? 'from-rose-400/25 to-rose-500/5 border-rose-400/30'
        : tone === 'blue'
          ? 'from-blue-400/25 to-blue-500/5 border-blue-400/30'
          : 'from-cyan-400/25 to-cyan-500/5 border-cyan-400/30'

  return (
    <div className={`rounded-3xl border bg-gradient-to-br p-5 ${toneClass} glass-panel-soft`}>
      <div className="text-sm text-slate-300">{label}</div>
      <div className="mt-3 text-4xl font-black tracking-tight text-white">{value}</div>
      <div className="mt-2 text-sm text-slate-400">{detail}</div>
    </div>
  )
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'info' }) {
  const toneClass =
    tone === 'success'
      ? 'border-emerald-400/40 bg-emerald-400/10 text-emerald-200'
      : tone === 'warning'
        ? 'border-amber-400/40 bg-amber-400/10 text-amber-200'
        : tone === 'danger'
          ? 'border-rose-400/40 bg-rose-400/10 text-rose-200'
          : tone === 'info'
            ? 'border-cyan-400/40 bg-cyan-400/10 text-cyan-200'
            : 'border-slate-600 bg-slate-900/60 text-slate-200'

  return <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold ${toneClass}`}>{children}</span>
}

export function DataTable({
  columns,
  rows,
}: {
  columns: string[]
  rows: ReactNode[][]
}) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-700/60 bg-slate-950/55">
      <table className="min-w-full border-collapse text-left text-sm">
        <thead className="bg-slate-900/70 text-slate-300">
          <tr>
            {columns.map((column) => (
              <th key={column} className="px-4 py-3 font-semibold">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-t border-slate-800/80 even:bg-slate-900/20">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-3 align-top text-slate-200">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function ActionButton({ children, href, kind = 'primary' }: { children: ReactNode; href: string; kind?: 'primary' | 'secondary' }) {
  const className = kind === 'primary' ? 'button-primary' : 'button-secondary'
  return (
    <Link href={href} className={className}>
      {children}
    </Link>
  )
}

export function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-2 overflow-hidden rounded-full bg-slate-800">
      <div className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-blue-500" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  )
}
