"use client"

import { useState } from 'react'

import { ActionButton, Badge, PortalShell, SectionCard, StatCard } from '@/components/portal'
import { professorAvailability, professorRequests } from '@/lib/site-data'

export default function ProfessorDashboardPage() {
  const [activeRequest, setActiveRequest] = useState(professorRequests[0].id)

  return (
    <PortalShell
      title="Profesor dashboard"
      subtitle="Inbox zahteva, availability pregled i brza odobravanja."
      badge="Professor portal"
      actions={<ActionButton href="/professor/settings" kind="secondary">Podešavanja</ActionButton>}
    >
      <section className="grid gap-4 md:grid-cols-4">
        <StatCard label="Zahtevi" value="7" detail="Čeka odobrenje" tone="cyan" />
        <StatCard label="Otvoreni slotovi" value="12" detail="Po nedelji" tone="blue" />
        <StatCard label="FAQ stavke" value="8" detail="Na profilu profesora" tone="green" />
        <StatCard label="Canned replies" value="4" detail="Spremno za odbijanje" tone="red" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <SectionCard eyebrow="Inbox" title="Pristigli zahtevi" description="Manual approve tok, delegiranje i brzi odgovori.">
          <div className="space-y-3">
            {professorRequests.map((request) => (
              <button
                key={request.id}
                onClick={() => setActiveRequest(request.id)}
                className={`w-full rounded-3xl border p-4 text-left transition ${activeRequest === request.id ? 'border-cyan-300/70 bg-cyan-300/10' : 'border-slate-700 bg-slate-950/55 hover:border-slate-500'}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="font-bold text-white">{request.student}</div>
                    <div className="mt-1 text-sm text-slate-300">{request.topic} · {request.time}</div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <Badge tone="warning">{request.status}</Badge>
                    <Badge tone="info">{request.mode}</Badge>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Actions" title="Quick approve panel" description="Ovo je mesto za approve/reject, delegiranje i canned response izbor.">
          <div className="space-y-4">
            <div className="rounded-3xl border border-slate-700 bg-slate-950/55 p-5">
              <div className="text-sm text-slate-400">Odabrani zahtev</div>
              <div className="mt-2 text-2xl font-bold text-white">{professorRequests.find((item) => item.id === activeRequest)?.student}</div>
              <p className="mt-2 text-sm text-slate-300">Ovo mesto će kasnije biti spojeno sa backend approve/reject endpoint-om.</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <ActionButton href="/appointments/appt-1">Otvori termin</ActionButton>
              <ActionButton href="/professor/settings" kind="secondary">Šabloni odgovora</ActionButton>
            </div>
          </div>
        </SectionCard>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SectionCard eyebrow="Availability" title="Recurring slots" description="Brzi pregled ponavljajućih slotova. U finalnoj verziji ovde ide FullCalendar drag-and-drop.">
          <div className="space-y-3">
            {professorAvailability.map((slot) => (
              <div key={slot.day} className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold text-white">{slot.day}</div>
                    <div className="mt-1 text-sm text-slate-400">{slot.hours} · {slot.type}</div>
                  </div>
                  <Badge tone="success">{slot.seats} seat(s)</Badge>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Metrics" title="Praćenje toka" description="Visual indicator stanja procesa u profesor panelu.">
          <div className="space-y-4 text-sm text-slate-300">
            <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">Auto-approve slotovi: uključeni za standardne termine</div>
            <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">Delegiranje asistentu: spremno za dodelu po predmetu</div>
            <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">CRM beleške: dostupne samo osoblju</div>
          </div>
        </SectionCard>
      </section>
    </PortalShell>
  )
}
