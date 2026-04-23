import Link from 'next/link'

import { ActionButton, Badge, SectionCard, StatCard } from '@/components/portal'
import { overviewStats } from '@/lib/site-data'

const toneToCardTone = (tone: string) => {
  if (tone === 'blue') return 'blue' as const
  if (tone === 'green') return 'green' as const
  if (tone === 'red') return 'red' as const
  return 'cyan' as const
}

export default function Home() {
  return (
    <div className="page-grid min-h-screen px-4 py-6 text-white md:px-8 md:py-10">
      <div className="mx-auto max-w-7xl space-y-8">
        <header className="glass-panel flex flex-col gap-6 p-6 md:flex-row md:items-center md:justify-between md:p-8">
          <div>
            <Badge tone="info">Studentska Platforma · MVP</Badge>
            <h1 className="hero-title mt-5">Univerzitetske konsultacije bez haosa</h1>
            <p className="hero-copy mt-5">
              Sistem za studente, profesore, asistente i administraciju. Zakazivanje, obaveštenja, chat, fajlovi i administracija na jednom mestu.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <ActionButton href="/login">Prijava</ActionButton>
            <ActionButton href="/dashboard" kind="secondary">Uđi u aplikaciju</ActionButton>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-4">
          {overviewStats.map((stat) => (
            <StatCard key={stat.label} label={stat.label} value={stat.value} detail={stat.detail} tone={toneToCardTone(stat.tone)} />
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <SectionCard eyebrow="Zašto platforma" title="Sve ključne akcije u jednom UI" description="Nema ručnog prebacivanja između mailova, Excel-a i poruka.">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-3xl border border-slate-700 bg-slate-950/55 p-5">
                <div className="text-lg font-bold">Studenti</div>
                <p className="mt-2 text-sm leading-6 text-slate-300">Pretraga profesora, zakazivanje termina, upload materijala, chat i istorija konsultacija.</p>
              </div>
              <div className="rounded-3xl border border-slate-700 bg-slate-950/55 p-5">
                <div className="text-lg font-bold">Profesori</div>
                <p className="mt-2 text-sm leading-6 text-slate-300">Recurring availability, blackout datumi, odobravanje zahteva i kratke odgovore kroz šablone.</p>
              </div>
              <div className="rounded-3xl border border-slate-700 bg-slate-950/55 p-5">
                <div className="text-lg font-bold">Admin</div>
                <p className="mt-2 text-sm leading-6 text-slate-300">CRUD korisnika, bulk import, impersonacija i masovna obaveštenja sa audit tragom.</p>
              </div>
              <div className="rounded-3xl border border-slate-700 bg-slate-950/55 p-5">
                <div className="text-lg font-bold">Operativa</div>
                <p className="mt-2 text-sm leading-6 text-slate-300">Redis locking, notifications, Celery jobs i MinIO uploadovi su već projektovani u backendu.</p>
              </div>
            </div>
          </SectionCard>

          <SectionCard eyebrow="Status rada" title="Šta je trenutno spremno" description="Ispod je vizuelni pregled glavnih tokova koje možeš odmah otvoriti.">
            <div className="space-y-3">
              {[
                ['Dashboard', '/dashboard'],
                ['Pretraga', '/search'],
                ['Profesor profil', '/professor/prof-1'],
                ['Termini', '/appointments/appt-1'],
                ['Admin panel', '/admin'],
              ].map(([label, href]) => (
                <Link key={href} href={href} className="flex items-center justify-between rounded-2xl border border-slate-700 bg-slate-950/55 px-4 py-4 transition hover:border-cyan-400/60 hover:bg-slate-900/80">
                  <span className="font-medium text-white">{label}</span>
                  <span className="text-sm text-cyan-300">Otvori →</span>
                </Link>
              ))}
            </div>
          </SectionCard>
        </section>
      </div>
    </div>
  )
}
