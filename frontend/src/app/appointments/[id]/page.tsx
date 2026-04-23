"use client"

import { useMemo, useState } from 'react'

import { ActionButton, Badge, PortalShell, SectionCard } from '@/components/portal'
import { appointmentFiles, chatMessages, studentAppointments } from '@/lib/site-data'

export default function AppointmentPage({ params }: { params: { id: string } }) {
  const appointment = useMemo(() => studentAppointments.find((item) => item.id === params.id) ?? studentAppointments[0], [params.id])
  const [messages, setMessages] = useState(chatMessages)
  const [message, setMessage] = useState('')

  function sendMessage() {
    if (!message.trim()) {
      return
    }

    setMessages((current) => [
      ...current,
      { id: `${Date.now()}`, sender: 'Student', text: message.trim(), time: new Date().toLocaleTimeString('sr-RS', { hour: '2-digit', minute: '2-digit' }) },
    ])
    setMessage('')
  }

  return (
    <PortalShell
      title={`Termin: ${appointment.professor}`}
      subtitle={`${appointment.subject} · ${appointment.scheduledAt} · ${appointment.mode}`}
      badge="Appointment detail"
      actions={<ActionButton href="/dashboard" kind="secondary">Nazad na dashboard</ActionButton>}
    >
      <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <SectionCard eyebrow="Detalji" title={appointment.topic} description="Chat, fajlovi i status termina na jednom mestu.">
          <div className="flex flex-wrap gap-2">
            <Badge tone={appointment.status === 'APPROVED' ? 'success' : appointment.status === 'PENDING' ? 'warning' : 'neutral'}>{appointment.status}</Badge>
            <Badge tone="info">{appointment.mode}</Badge>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-300">
            Ovaj ekran pokriva deo PRD-a za detalje termina, grupne konsultacije, fajlove i ticket chat.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <ActionButton href="#chat">Otvori chat</ActionButton>
            <ActionButton href="#files" kind="secondary">Fajlovi</ActionButton>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Files" title="Materijali za konsultaciju" description="Upload preko MinIO backend layer-a.">
          <div id="files" className="space-y-3">
            {appointmentFiles.map((file) => (
              <div key={file.id} className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">{file.name}</div>
                    <div className="mt-1 text-sm text-slate-400">{file.uploadedBy} · {file.createdAt}</div>
                  </div>
                  <Badge tone="info">{file.size}</Badge>
                </div>
              </div>
            ))}
            <div className="rounded-2xl border border-dashed border-slate-600 bg-slate-950/30 p-5 text-sm text-slate-400">
              Upload fajlova je ograničen na 5 MB po fajlu i radi preko MinIO storage sloja.
            </div>
          </div>
        </SectionCard>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <SectionCard eyebrow="Chat" title="In-app ticket chat" description="WebSocket u finalnoj verziji, ovde demo tok poruka radi odmah.">
          <div id="chat" className="space-y-4">
            <div className="space-y-3 rounded-3xl border border-slate-700 bg-slate-950/55 p-4">
              {messages.map((item) => (
                <div key={item.id} className={`max-w-[85%] rounded-2xl px-4 py-3 ${item.sender === 'Student' ? 'ml-auto bg-cyan-400/10 border border-cyan-400/20' : 'bg-slate-900/75 border border-slate-700'}`}>
                  <div className="flex items-center justify-between gap-3 text-xs text-slate-400">
                    <span className="font-semibold text-white">{item.sender}</span>
                    <span>{item.time}</span>
                  </div>
                  <div className="mt-2 text-sm leading-6 text-slate-200">{item.text}</div>
                </div>
              ))}
            </div>
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <input className="input" value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Napiši novu poruku..." />
              <button className="button-primary" onClick={sendMessage}>Pošalji</button>
            </div>
          </div>
        </SectionCard>

        <SectionCard eyebrow="Group" title="Grupne konsultacije" description="Tagovanje kolega i potvrde dolaska su deo workflow-a.">
          <div className="space-y-3 text-sm text-slate-300">
            <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">Vođa tima: student koji kreira termin</div>
            <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">Tagovani članovi: dobijaju notifikaciju i potvrđuju dolazak</div>
            <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">Ako ne potvrde: nisu evidentirani, ali termin ostaje aktivan</div>
          </div>
        </SectionCard>
      </section>
    </PortalShell>
  )
}
