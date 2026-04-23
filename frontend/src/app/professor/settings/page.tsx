"use client"

import { useState } from 'react'

import { ActionButton, Badge, PortalShell, SectionCard } from '@/components/portal'
import { cannedResponses, professorAvailability } from '@/lib/site-data'

export default function ProfessorSettingsPage() {
  const [newFaqQuestion, setNewFaqQuestion] = useState('')
  const [newFaqAnswer, setNewFaqAnswer] = useState('')

  return (
    <PortalShell
      title="Profesor settings"
      subtitle="Availability, canned responses i FAQ menadžment."
      badge="Professor settings"
      actions={<ActionButton href="/professor/dashboard" kind="secondary">Nazad</ActionButton>}
    >
      <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <SectionCard eyebrow="Availability editor" title="Recurring slot konfiguracija" description="Ovde profesor definiše dane, vreme i tip konsultacija.">
          <div className="space-y-3">
            {professorAvailability.map((slot) => (
              <div key={slot.day} className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">{slot.day}</div>
                    <div className="mt-1 text-sm text-slate-400">{slot.hours} · {slot.type}</div>
                  </div>
                  <Badge tone="info">{slot.seats} seat(s)</Badge>
                </div>
              </div>
            ))}
            <div className="rounded-2xl border border-dashed border-slate-600 bg-slate-950/35 p-4 text-sm text-slate-400">Drag-and-drop editor će se kasnije vezati za FullCalendar.</div>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Canned responses" title="Brzi odgovori" description="Kratki tekstovi za reject/delegation workflow.">
          <div className="space-y-3">
            {cannedResponses.map((response) => (
              <div key={response} className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4 text-sm leading-6 text-slate-300">{response}</div>
            ))}
            <input className="input" value={newFaqQuestion} onChange={(event) => setNewFaqQuestion(event.target.value)} placeholder="Nova FAQ tema" />
            <textarea className="textarea min-h-[120px]" value={newFaqAnswer} onChange={(event) => setNewFaqAnswer(event.target.value)} placeholder="Odgovor za FAQ ili templated response" />
            <div className="flex flex-wrap gap-3">
              <ActionButton href="#">Sačuvaj lokално</ActionButton>
              <ActionButton href="#" kind="secondary">Dodaj u šablone</ActionButton>
            </div>
          </div>
        </SectionCard>
      </section>
    </PortalShell>
  )
}
