"use client"

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'

import { ActionButton, Badge, PortalShell, SectionCard } from '@/components/portal'
import { safeJson } from '@/lib/api'
import { professors } from '@/lib/site-data'

type SearchResult = {
  professor_id: string
  full_name: string
  department?: string | null
  title?: string | null
  office_number?: string | null
  subjects?: string[]
  highlights?: string[]
  availability_hint?: string | null
}

type ProfessorCard = {
  id: string
  name: string
  department: string
  title: string
  office: string
  bio: string
  subjects: string[]
  availability: string[]
  highlights: string[]
  source: 'backend' | 'local'
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [department, setDepartment] = useState('')
  const [subject, setSubject] = useState('')
  const [backendResults, setBackendResults] = useState<SearchResult[] | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    let isActive = true

    async function loadResults() {
      setIsLoading(true)
      const params = new URLSearchParams()

      if (query.trim()) {
        params.set('q', query.trim())
      }
      if (department.trim()) {
        params.set('department', department.trim())
      }
      if (subject.trim()) {
        params.set('subject', subject.trim())
      }
      params.set('limit', '12')

      const data = await safeJson<SearchResult[]>(`/v1/search?${params.toString()}`, {
        signal: controller.signal,
      })

      if (!isActive) {
        return
      }

      setBackendResults(data)
      setIsLoading(false)
    }

    loadResults()

    return () => {
      isActive = false
      controller.abort()
    }
  }, [department, query, subject])

  const fallbackResults = useMemo(() => {
    const q = query.trim().toLowerCase()

    return professors.filter((professor) => {
      const haystack = [
        professor.firstName,
        professor.lastName,
        professor.department,
        professor.title,
        professor.bio,
        ...professor.subjects,
        ...professor.keywords,
      ]
        .join(' ')
        .toLowerCase()

      const departmentOk = !department || professor.department.toLowerCase().includes(department.toLowerCase())
      const subjectOk = !subject || professor.subjects.some((item) => item.toLowerCase().includes(subject.toLowerCase()))
      const queryOk = !q || haystack.includes(q)

      return departmentOk && subjectOk && queryOk
    })
  }, [department, query, subject])

  const results: ProfessorCard[] = backendResults && backendResults.length > 0
    ? backendResults.map((item) => ({
        id: item.professor_id,
        name: item.full_name,
        department: item.department || 'Nepoznata katedra',
        title: item.title || 'Profesor',
        office: item.office_number || 'TBA',
        bio: item.availability_hint || 'Backend rezultat pretrage profesora',
        subjects: item.subjects || [],
        availability: item.availability_hint ? [item.availability_hint] : ['Slobodno'],
        highlights: item.highlights || [],
        source: 'backend',
      }))
    : fallbackResults.map((professor) => ({
        id: professor.id,
        name: `${professor.firstName} ${professor.lastName}`,
        department: professor.department,
        title: professor.title,
        office: professor.office,
        bio: professor.bio,
        subjects: professor.subjects,
        availability: professor.availability,
        highlights: professor.faq.slice(0, 2).map((item) => item.question),
        source: 'local',
      }))

  return (
    <PortalShell
      title="Pretraga profesora"
      subtitle="Filtriraj po imenu, katedri, predmetu ili ključnim rečima. Ovo je ulazna tačka za student booking flow."
      badge="Student search"
      actions={<ActionButton href="/dashboard" kind="secondary">Nazad na dashboard</ActionButton>}
    >
      <SectionCard eyebrow="Filteri" title="Nađi profesora u nekoliko sekundi" description="Živa pretraga preko backend search endpoint-a, sa lokalnim fallbackom kad API nije dostupan.">
        <div className="grid gap-4 md:grid-cols-3">
          <input className="input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ime, predmet ili keyword" />
          <input className="input" value={department} onChange={(event) => setDepartment(event.target.value)} placeholder="Katedra ili odsek" />
          <input className="input" value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Predmet" />
        </div>
        <div className="mt-4 text-sm text-slate-400">
          {isLoading ? 'Tražim rezultate na backendu...' : backendResults ? 'Rezultati dolaze iz backend search API-ja.' : 'Backend trenutno nije dostupan, prikazujem lokalne podatke.'}
        </div>
      </SectionCard>

      <div className="grid gap-4 lg:grid-cols-2">
        {results.map((professor) => (
          <SectionCard key={professor.id} eyebrow={professor.department} title={professor.name} description={professor.bio}>
            <div className="flex flex-wrap gap-2">
              <Badge tone="info">{professor.title}</Badge>
              <Badge tone="success">Kabinet {professor.office}</Badge>
              <Badge tone={professor.source === 'backend' ? 'success' : 'warning'}>{professor.source === 'backend' ? 'Backend' : 'Local fallback'}</Badge>
            </div>
            <div className="mt-4 space-y-3 text-sm text-slate-300">
              <div><span className="text-slate-500">Predmeti:</span> {professor.subjects.join(', ') || 'Nema dostupnih predmeta'}</div>
              <div><span className="text-slate-500">Availability:</span> {professor.availability.join(' · ')}</div>
              <div><span className="text-slate-500">Highlights:</span> {professor.highlights.slice(0, 2).join(' · ') || 'Nema posebnih highlight-a'}</div>
            </div>
            <div className="mt-5 flex flex-wrap gap-3">
              <ActionButton href={`/professor/${professor.id}`}>Otvori profil</ActionButton>
              <Link href="/appointments/appt-1" className="button-secondary">Zakaži konsultaciju</Link>
            </div>
          </SectionCard>
        ))}
      </div>
    </PortalShell>
  )
}
