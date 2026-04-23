import { ActionButton, Badge, SectionCard } from '@/components/portal'
import { authRedirectUrl } from '@/lib/api'

export default function LoginPage() {
  return (
    <div className="page-grid min-h-screen px-4 py-6 text-white md:px-8 md:py-10">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-6xl items-center">
        <div className="grid w-full gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="glass-panel relative overflow-hidden p-8 md:p-12">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(94,234,212,0.18),transparent_30%),radial-gradient(circle_at_bottom_left,rgba(96,165,250,0.12),transparent_28%)]" />
            <div className="relative">
              <Badge tone="info">Keycloak SSO</Badge>
              <h1 className="hero-title mt-5 max-w-2xl">Prijava u Studentsku Platformu</h1>
              <p className="hero-copy mt-5">
                Ulazak je moguć samo preko fakultetskog naloga. Nakon prijave dobijaš pristup dashboard-u, pretrazi profesora, terminima, porukama i administraciji prema ulozi.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <a href={authRedirectUrl()} className="button-primary">Prijavi se preko Keycloak-a</a>
                <ActionButton href="/dashboard" kind="secondary">Demo dashboard</ActionButton>
              </div>

              <div className="mt-10 grid gap-4 md:grid-cols-3">
                <div className="rounded-3xl border border-slate-700 bg-slate-950/55 p-4">
                  <div className="text-sm text-slate-400">Student</div>
                  <div className="mt-2 text-lg font-bold">Zakazivanje, notifikacije, fajlovi</div>
                </div>
                <div className="rounded-3xl border border-slate-700 bg-slate-950/55 p-4">
                  <div className="text-sm text-slate-400">Profesor</div>
                  <div className="mt-2 text-lg font-bold">Availability, odobravanje, chat</div>
                </div>
                <div className="rounded-3xl border border-slate-700 bg-slate-950/55 p-4">
                  <div className="text-sm text-slate-400">Admin</div>
                  <div className="mt-2 text-lg font-bold">CRUD, import, broadcast, audit</div>
                </div>
              </div>
            </div>
          </section>

          <aside className="space-y-6">
            <SectionCard eyebrow="Brzi pregled" title="Šta je dostupno odmah" description="Ovo je funkcionalni MVP bez V2 AI sloja.">
              <div className="space-y-3 text-sm text-slate-300">
                <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">Pregled termina i istorije</div>
                <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">Pretraga profesora i njihovih slotova</div>
                <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">Chat po terminu i upload fajlova</div>
                <div className="rounded-2xl border border-slate-700 bg-slate-950/55 p-4">Admin panel sa importom i impersonacijom</div>
              </div>
            </SectionCard>
          </aside>
        </div>
      </div>
    </div>
  )
}
