"use client"

import { useMemo, useState } from 'react'

import { ActionButton, Badge, PortalShell, SectionCard } from '@/components/portal'
import { appointmentFiles, chatMessages, professors } from '@/lib/site-data'

export default function ProfessorProfilePage({ params }: { params: { id: string } }) {
  const professor = useMemo(() => professors.find((item) => item.id === params.id) ?? professors[0], [params.id])
  const [topic, setTopic] = useState('Seminarski rad')
  const [description, setDescription] = useState('')
  const [selectedSlot, setSelectedSlot] = useState(professor.availability[0])

  return (
    <PortalShell
      title={`${professor.firstName} ${professor.lastName}`}
      subtitle={`${professor.title} · ${professor.department} · kabinet ${professor.office}`}
      badge="Professor profile"
      actions={<ActionButton href="/search" kind="secondary">Nazad na pretragu</ActionButton>}
    >
      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <SectionCard eyebrow="Profil" title="Mini-profil i FAQ" description="Student prvo vidi informacije i dostupne slotove, pa tek onda kreće booking flow.">
          <div className="space-y-4">
            <div className="rounded-3xl border border-slate-700 bg-slate-950/55 p-5">
              <div className="flex flex-wrap gap-2">
                <Badge tone="info">{professor.title}</Badge>
                <Badge tone="success">Kabinet {professor.office}</Badge>
              </div>
              <p className="mt-4 text-sm leading-6 text-slate-300">{professor.bio}</p>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              {professor.faq.map((item) => (
                <div key={item.question} className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">
                  <div className="font-semibold text-white">{item.question}</div>
                  <div className="mt-2 text-sm leading-6 text-slate-300">{item.answer}</div>
                </div>
              ))}
            </div>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Booking" title="Zakaži termin" description="Demo forma za izbor teme, slot-a i opisa. U finalu bi ovo išlo kroz Redis lock i backend booking endpoint.">
          <div className="space-y-4">
            <select className="select" value={topic} onChange={(event) => setTopic(event.target.value)}>
              <option>Seminarski rad</option>
              <option>Predavanja / teorija</option>
              <option>Priprema za ispit</option>
              <option>Projekat / praktičan rad</option>
              <option>Ostalo</option>
            </select>
            <select className="select" value={selectedSlot} onChange={(event) => setSelectedSlot(event.target.value)}>
              {professor.availability.map((slot) => (
                <option key={slot}>{slot}</option>
              ))}
            </select>
            <textarea className="textarea min-h-[150px]" value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Kratak opis problema i šta tačno želiš da rešiš." />
            <div className="flex flex-wrap gap-3">
              <ActionButton href="/appointments/appt-1">Kreiraj zahtev</ActionButton>
              <ActionButton href="#files" kind="secondary">Dodaj fajlove</ActionButton>
            </div>
            <div className="text-sm text-slate-400">Tema: {topic} · Slot: {selectedSlot} · Dužina opisa: {description.length} karaktera</div>
          </div>
        </SectionCard>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SectionCard eyebrow="Slotovi" title="Slobodni termini" description="Vizuelni prikaz dostupnosti za naredni period.">
          <div className="space-y-3">
            {professor.availability.map((slot) => (
              <div key={slot} className="flex items-center justify-between rounded-2xl border border-slate-700 bg-slate-950/55 px-4 py-4">
                <div className="font-medium text-white">{slot}</div>
                <Badge tone="success">Slobodno</Badge>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Recent files" title="Materijali u terminu" description="Upload i download preko MinIO layer-a u backendu.">
          <div id="files" className="space-y-3">
            {appointmentFiles.map((file) => (
              <div key={file.id} className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <div className="font-semibold text-white">{file.name}</div>
                    <div className="mt-1 text-sm text-slate-400">{file.uploadedBy} · {file.createdAt}</div>
                  </div>
                  <Badge tone="info">{file.size}</Badge>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>
      </section>
    </PortalShell>
  )
}
