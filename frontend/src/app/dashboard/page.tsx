"use client"

import Link from 'next/link'
import { useState } from 'react'

import { ActionButton, Badge, PortalShell, ProgressBar, SectionCard, StatCard, DataTable } from '@/components/portal'
import { notifications, overviewStats, studentAppointments } from '@/lib/site-data'

export default function DashboardPage() {
  const [selected, setSelected] = useState(studentAppointments[0].id)

  const selectedAppointment = studentAppointments.find((appointment) => appointment.id === selected) ?? studentAppointments[0]

  return (
    <PortalShell
      title="Student dashboard"
      subtitle="Pregled nadolazećih termina, poruka i brzih akcija. Ovo je prva radna stanica za studenta po PRD-u."
      badge="Student portal"
      actions={
        <>
          <ActionButton href="/search">Pretraga profesora</ActionButton>
          <ActionButton href="/my-appointments" kind="secondary">Moji termini</ActionButton>
        </>
      }
    >
      <section className="grid gap-4 md:grid-cols-4">
        {overviewStats.map((stat) => (
          <StatCard key={stat.label} label={stat.label} value={stat.value} detail={stat.detail} tone={stat.tone as any} />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <SectionCard eyebrow="Nadolazeći termini" title="Sve što dolazi uskoro" description="Klikni na karticu termina da otvoriš detalje, chat i fajlove.">
          <div className="space-y-3">
            {studentAppointments.map((appointment) => (
              <button
                key={appointment.id}
                onClick={() => setSelected(appointment.id)}
                className={`w-full rounded-3xl border p-4 text-left transition ${selected === appointment.id ? 'border-cyan-300/70 bg-cyan-300/10' : 'border-slate-700 bg-slate-950/55 hover:border-slate-500 hover:bg-slate-900/80'}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-lg font-bold text-white">{appointment.professor}</div>
                    <div className="mt-1 text-sm text-slate-300">{appointment.subject} · {appointment.topic}</div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <Badge tone={appointment.status === 'APPROVED' ? 'success' : appointment.status === 'PENDING' ? 'warning' : 'neutral'}>{appointment.status}</Badge>
                    <span className="text-xs text-slate-400">{appointment.scheduledAt}</span>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Brza akcija" title={selectedAppointment.professor} description={`Termin: ${selectedAppointment.scheduledAt} · ${selectedAppointment.mode}`}>
          <div className="space-y-4">
            <div className="rounded-3xl border border-slate-700 bg-slate-950/55 p-5">
              <div className="section-title">Detalji</div>
              <div className="mt-3 text-2xl font-bold text-white">{selectedAppointment.topic}</div>
              <p className="mt-2 text-sm leading-6 text-slate-300">
                Ovaj panel bi u finalnoj verziji pokazivao status termina, dugmad za otkazivanje, otvaranje chata i upload fajlova.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge tone="info">{selectedAppointment.mode}</Badge>
                <Badge tone={selectedAppointment.status === 'APPROVED' ? 'success' : 'warning'}>{selectedAppointment.status}</Badge>
              </div>
            </div>
            <div>
              <div className="mb-2 text-sm text-slate-400">Status ka finalnom predlogu</div>
              <ProgressBar value={selectedAppointment.status === 'APPROVED' ? 85 : selectedAppointment.status === 'PENDING' ? 55 : 100} />
            </div>
            <div className="flex flex-wrap gap-3">
              <ActionButton href={`/appointments/${selectedAppointment.id}`}>Otvori termin</ActionButton>
              <ActionButton href={`/professor/${selectedAppointment.professorId}`} kind="secondary">Profil profesora</ActionButton>
            </div>
          </div>
        </SectionCard>
      </section>

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <SectionCard eyebrow="Notifikacije" title="Šta je stiglo" description="In-app centar obaveštenja i brz pregled poslednjih poruka.">
          <div className="space-y-3">
            {notifications.map((item) => (
              <div key={item.id} className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-semibold text-white">{item.title}</div>
                  <span className="text-xs text-slate-400">{item.time}</span>
                </div>
                <div className="mt-2 text-sm leading-6 text-slate-300">{item.message}</div>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard eyebrow="Akcije" title="Šta korisnik može odmah" description="Direktni tokovi za učenika bez skrivenih koraka.">
          <DataTable
            columns={["Akcija", "Opis", "Putanja"]}
            rows={[
              ['Pretraga profesora', 'Filtriranje po predmetu i keyword-u', '/search'],
              ['Zakazivanje', 'Kreiranje request-a i pratećih fajlova', '/professor/prof-1'],
              ['Chat', 'Poruke po terminu i fajlovi', '/appointments/appt-1'],
              ['Istorija', 'Upad i completed termini', '/my-appointments'],
            ].map((row) => row.map((cell) => <span key={cell as string}>{cell}</span>))}
          />
        </SectionCard>
      </section>
    </PortalShell>
  )
}
