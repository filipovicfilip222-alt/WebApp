"use client"

import { useEffect, useMemo, useState } from 'react'

import { ActionButton, Badge, DataTable, PortalShell, SectionCard, StatCard } from '@/components/portal'
import { apiUrl, getAuthTokenForForms, requestJson, safeJson } from '@/lib/api'
import { adminUsers, auditLogs } from '@/lib/site-data'

type BackendUser = {
  id: string
  first_name: string
  last_name: string
  email: string
  user_role: string
  is_active: boolean
}

export default function AdminPage() {
  const [broadcastTitle, setBroadcastTitle] = useState('')
  const [broadcastMessage, setBroadcastMessage] = useState('')
  const [importState, setImportState] = useState('')
  const [users, setUsers] = useState<BackendUser[] | null>(null)
  const [statusMessage, setStatusMessage] = useState('Spreman za backend sinhronizaciju.')
  const [isBusy, setIsBusy] = useState(false)
  const [csvFile, setCsvFile] = useState<File | null>(null)

  useEffect(() => {
    let mounted = true

    async function loadUsers() {
      const data = await safeJson<BackendUser[]>('/v1/admin/users')
      if (!mounted) {
        return
      }

      if (data && data.length > 0) {
        setUsers(data)
        setStatusMessage('Učitani korisnici iz backend admin API-ja.')
        return
      }

      setUsers(null)
      setStatusMessage('Backend admin API nije dostupan, koristi se lokalni fallback.')
    }

    loadUsers()

    return () => {
      mounted = false
    }
  }, [])

  const activeUsers = useMemo(() => {
    if (users && users.length > 0) {
      return users.map((user) => ({
        id: user.id,
        name: `${user.first_name} ${user.last_name}`,
        email: user.email,
        role: user.user_role,
        active: user.is_active,
      }))
    }

    return adminUsers
  }, [users])

  async function handleBroadcast() {
    setIsBusy(true)
    const result = await requestJson<{ status: string; recipient_count: number }>('/v1/admin/broadcast', {
      method: 'POST',
      body: JSON.stringify({
        title: broadcastTitle || 'Obaveštenje sa admin panela',
        message: broadcastMessage || 'Demo broadcast iz admin ekrana',
        audience: 'all',
      }),
    })

    if (result) {
      setStatusMessage(`Broadcast poslat ka ${result.recipient_count} korisnika.`)
    } else {
      setStatusMessage('Broadcast nije uspeo preko backend-a, ali forma je spremna za konekciju.')
    }

    setIsBusy(false)
  }

  async function handleImport() {
    if (!csvFile) {
      setStatusMessage('Izaberi CSV fajl pre importa.')
      return
    }

    setIsBusy(true)
    const formData = new FormData()
    formData.append('file', csvFile)

    const token = getAuthTokenForForms()
    const response = await fetch(apiUrl('/v1/admin/import/students'), {
      method: 'POST',
      body: formData,
      headers: token ? { Authorization: token.startsWith('Bearer ') ? token : `Bearer ${token}` } : undefined,
    }).catch(() => null)

    if (response && response.ok) {
      const data = (await response.json()) as { created: number; skipped: number }
      setStatusMessage(`Import završen: ${data.created} kreirano, ${data.skipped} preskočeno.`)
    } else {
      setStatusMessage('CSV import endpoint nije dostupan, ali preview radi lokalno.')
    }

    setIsBusy(false)
  }

  return (
    <PortalShell
      title="Admin panel"
      subtitle="CRUD korisnika, import, impersonacija, broadcast i audit log."
      badge="Admin panel"
      actions={<ActionButton href="/dashboard" kind="secondary">Nazad</ActionButton>}
    >
      <section className="grid gap-4 md:grid-cols-4">
        <StatCard label="Korisnici" value={String(activeUsers.length)} detail={users ? 'Iz backend admin API-ja' : 'Lokalni fallback'} tone="cyan" />
        <StatCard label="Audit zapisi" value={String(auditLogs.length)} detail="Impersonacija i broadcast" tone="blue" />
        <StatCard label="Import status" value={csvFile ? 'Ready' : 'Idle'} detail={csvFile ? csvFile.name : 'CSV import pipeline'} tone="green" />
        <StatCard label="Broadcast" value={isBusy ? 'Sending' : 'Live'} detail="In-app + email layer" tone="red" />
      </section>

      <div className="rounded-3xl border border-cyan-400/20 bg-cyan-400/10 px-5 py-4 text-sm text-cyan-50">
        {statusMessage}
      </div>

      <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <SectionCard eyebrow="Users" title="Centralni registar korisnika" description="Pregled, aktivacija, deaktivacija i role management.">
          <DataTable
            columns={["Ime", "Email", "Uloga", "Status"]}
            rows={activeUsers.map((user) => [
              <span key={`${user.id}-name`}>{user.name}</span>,
              <span key={`${user.id}-email`}>{user.email}</span>,
              <span key={`${user.id}-role`}><Badge tone="info">{user.role}</Badge></span>,
              <span key={`${user.id}-status`}><Badge tone={user.active ? 'success' : 'danger'}>{user.active ? 'Active' : 'Disabled'}</Badge></span>,
            ])}
          />
        </SectionCard>

        <SectionCard eyebrow="Bulk import" title="CSV upload i preview" description="Koliko redova je pročitano i koliko je spremno za uvoz.">
          <div className="space-y-4">
            <input
              className="input"
              type="file"
              accept=".csv"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null
                setCsvFile(file)
                setImportState(file?.name ?? '')
              }}
            />
            <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4 text-sm text-slate-300">
              {importState ? `Odabran fajl: ${importState}` : 'Nije odabran nijedan CSV fajl.'}
            </div>
            <div className="flex flex-wrap gap-3">
              <button type="button" className="button-primary" onClick={() => setStatusMessage('Preview je spreman, import pokreće backend endpoint kada je dostupno.')}>Pokreni preview</button>
              <button type="button" className="button-secondary" onClick={handleImport} disabled={isBusy}>Importuj</button>
            </div>
          </div>
        </SectionCard>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <SectionCard eyebrow="Broadcast" title="Globalno obaveštenje" description="Baner, email i push tok za hitna saopštenja.">
          <div className="space-y-3">
            <input className="input" value={broadcastTitle} onChange={(event) => setBroadcastTitle(event.target.value)} placeholder="Naslov obaveštenja" />
            <textarea className="textarea min-h-[140px]" value={broadcastMessage} onChange={(event) => setBroadcastMessage(event.target.value)} placeholder="Poruka za studente/profesore" />
            <div className="flex flex-wrap gap-3">
              <button type="button" className="button-primary" onClick={handleBroadcast} disabled={isBusy}>Pošalji broadcast</button>
              <button type="button" className="button-secondary" onClick={() => setStatusMessage('Nacrt je lokalno pripremljen.')}>Sačuvaj nacrt</button>
            </div>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Audit log" title="Impersonacija i administrativne akcije" description="Svaka admin akcija se čuva kroz audit trag.">
          <div className="space-y-3">
            {auditLogs.map((log) => (
              <div key={log.id} className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4 text-sm text-slate-300">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-semibold text-white">{log.action}</div>
                  <Badge tone="info">{log.at}</Badge>
                </div>
                <div className="mt-2">Target: {log.target} · IP: {log.ip}</div>
              </div>
            ))}
          </div>
        </SectionCard>
      </section>
    </PortalShell>
  )
}
