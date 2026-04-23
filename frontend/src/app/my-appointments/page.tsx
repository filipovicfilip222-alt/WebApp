import { ActionButton, Badge, PortalShell, SectionCard, StatCard } from '@/components/portal'
import { studentAppointments, strikeRecords } from '@/lib/site-data'

export default function MyAppointmentsPage() {
  return (
    <PortalShell
      title="Moji termini"
      subtitle="Upcoming i istorija terminskih konsultacija sa pregledom kaznenih poena i statusa."
      badge="Student history"
      actions={<ActionButton href="/dashboard" kind="secondary">Nazad</ActionButton>}
    >
      <section className="grid gap-4 md:grid-cols-4">
        <StatCard label="Nadolazeći" value="2" detail="Termin u narednih 7 dana" tone="cyan" />
        <StatCard label="Završeni" value="1" detail="Istorija konsultacija" tone="blue" />
        <StatCard label="Strikes" value={String(strikeRecords.length)} detail="Aktivni kazneni poeni" tone="red" />
        <StatCard label="Blokiran" value="Ne" detail="Zakazivanje dostupno" tone="green" />
      </section>

      <SectionCard eyebrow="Pregled" title="Vremenska linija" description="Ovo je ono što student vidi na ličnoj istoriji termina.">
        <div className="space-y-3">
          {studentAppointments.map((appointment) => (
            <div key={appointment.id} className="rounded-3xl border border-slate-700 bg-slate-950/55 p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="text-xl font-bold text-white">{appointment.professor}</div>
                  <div className="mt-1 text-sm text-slate-300">{appointment.subject} · {appointment.scheduledAt}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge tone={appointment.status === 'APPROVED' ? 'success' : appointment.status === 'PENDING' ? 'warning' : 'neutral'}>{appointment.status}</Badge>
                  <Badge tone="info">{appointment.mode}</Badge>
                </div>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-400">Tema: {appointment.topic}</p>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard eyebrow="Kazne" title="Aktivni strike zapisi" description="Pravila otkazivanja i nepojavljivanja su aktivna u backend-u i vidljiva adminu.">
        <div className="space-y-3">
          {strikeRecords.map((strike) => (
            <div key={strike.id} className="rounded-3xl border border-rose-400/20 bg-rose-400/10 p-5">
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="text-lg font-bold text-white">{strike.student}</div>
                  <div className="mt-1 text-sm text-rose-100/80">{strike.reason} · ističe {strike.expires}</div>
                </div>
                <Badge tone="danger">{strike.points} poena</Badge>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </PortalShell>
  )
}
