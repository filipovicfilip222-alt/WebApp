# Specifikacija Zahteva Proizvoda (PRD)
## Platforma za upravljanje univerzitetskim konsultacijama i komunikacijom

**Status:** Odobreno  
**Verzija:** 1.1  
**Poslednja izmena:** April 2025  

---

## Sadržaj

1. [Arhitektura Sistema i Bezbednost](#1-arhitektura-sistema-i-bezbednost)
2. [Modul za Studente (Student Portal)](#2-modul-za-studente-student-portal)
3. [Modul za Profesore i Asistente (Staff Portal)](#3-modul-za-profesore-i-asistente-staff-portal)
4. [Modul za Studentsku Službu (Admin Panel)](#4-modul-za-studentsku-službu-admin-panel)
5. [Sistemski i Quality of Life Dodaci](#5-sistemski-i-quality-of-life-dodaci)
6. [Planirano za V2](#6-planirano-za-v2)

---

## 1. Arhitektura Sistema i Bezbednost

Sistem je dizajniran kao **visoko-bezbedna, zatvorena platforma (Intranet pristup)** namenjena isključivo akademskom osoblju i aktivnim studentima. Javni pristup nije dozvoljen ni u jednoj tački sistema.

### 1.1 Zatvorena Registracija

- Onemogućen javni "Sign Up" — ne postoji obrazac za samostalnu registraciju.
- Nalozi se **automatski provizioniraju** sinhronizacijom sa postojećim informacionim sistemom fakulteta:
  - Active Directory / LDAP sinhronizacija, **ili**
  - Direktni API poziv studentske službe pri upisu.
- Administrator može ručno kreirati nalog ili pokrenuti **Bulk Import** iz CSV fajla.

### 1.2 SSO (Single Sign-On)

- Autentifikacija se vrši **isključivo** preko zvaničnih fakultetskih naloga:
  - **G-Suite** (Google OAuth 2.0)
  - **Microsoft 365** (OpenID Connect)
- Nije podržan login sa privatnim (gmail.com, outlook.com) nalozima.
- Implementovano putem **Keycloak**-a (self-hosted, on-premise).

### 1.3 RBAC (Role-Based Access Control)

Sistem ima 4 strogo definisane uloge sa granularnim dozvolama:

| Uloga | Opis | Ključne dozvole |
|-------|------|-----------------|
| `STUDENT` | Aktivni student | Pretraga, zakazivanje, upload fajlova, chat |
| `ASISTENT` | Asistent na predmetu | Odobravanje/odbijanje termina, CRM beleške (samo za dodeljene predmete) |
| `PROFESOR` | Nastavno osoblje | Puno upravljanje kalendarom, delegiranje, šabloni, CRM |
| `ADMIN` | Studentska služba | CRUD svih korisnika, impersonacija, broadcast, strike menadžment |

> **Napomena:** Asistent može odobravati termine, ali **ne može** menjati globalni raspored profesora niti pristupati terminima van predmeta kojima je dodeljen.

---

## 2. Modul za Studente (Student Portal)

Fokus: brz pristup informacijama, minimalna frikcija pri zakazivanju, transparentnost procesa.

### 2.1 Otkrivanje i Pretraga Profesora

#### Smart Search & Filter
- Pretraga po: imenu, prezimenu, katedri, predmetu
- Pretraga po **ključnim rečima** (npr. "Mašinsko učenje", "Baze podataka") — algoritam pronalazi profesore koji su tagovani za te oblasti u svom profilu
- Filteri: tip konsultacija (Uživo / Online), dostupnost (slobodnih termina danas / ove nedelje)

#### Profili Profesora
Svaki profesor ima mini-profil koji sadrži:
- Profilna slika, zvanje, katedra
- Broj kabineta i mapa/opis lokacije
- Link do objavljenih radova (opciono)
- Lista predmeta koje predaje
- **FAQ sekcija** — Profesor postavlja najčešća pitanja i odgovore pre zakazivanja (npr. "Kako se brani seminarski?", "Format ispita?")

> **UX pravilo:** Student vidi FAQ **pre** nego što klikne na "Zakaži" — cilj je smanjiti broj nepotrebnih konsultacija.

---

### 2.2 Sistem Zakazivanja

#### Interaktivni Kalendar
- Prikaz slobodnih slotova u **realnom vremenu**
- Slot se vizuelno "zaključava" (blokira za ostale) u trenutku kada student počne proces zakazivanja (Redis pessimistic locking, TTL: 30 sekundi)

#### Tipovi Konsultacija
| Tip | Opis |
|-----|------|
| **Uživo** | Prikazuje broj i mapu kabineta |
| **Online** | Prikazuje Teams / Zoom link (generisan ili ručno unet od profesora) |

#### Kontekstualni Zahtev (obavezna polja)
Pri svakom zakazivanju student mora da unese:

1. **Tema** — Dropdown selektor:
   - Seminarski rad
   - Predavanja / Teorija
   - Priprema za ispit
   - Projekat / Praktičan rad
   - Ostalo (sa slobodnim tekstom)

2. **Kratak opis** — Tekstualno polje (min 20, max 500 karaktera)

3. **Fajlovi** (opciono) — Upload do **5MB** po terminu
   - Dozvoljeni formati: PDF, DOCX, XLSX, PNG, JPG, ZIP, .py, .java, .cpp (kod)
   - Čuvaju se u MinIO, ne u bazi

#### Grupne Konsultacije
- Vođa tima zakazuje termin i **taguje kolege** (po email-u ili korisničkom imenu)
- Tagovane kolege dobijaju notifikaciju i moraju **potvrditi dolazak** (rok: 24h)
- Ukoliko kolega ne potvrdi, termin ostaje važeći ali ta osoba neće biti evidentirana

#### Lista Čekanja (Waitlist)
- Aktivira se kada je profesor **potpuno bukiran** (nema slobodnih slotova)
- Student se prijavljuje na listu čekanja za željenog profesora ili specifičan slot
- Kada neko otkaže termin, sistem **automatski nudi** slobodan slot prvom studentu na listi:
  - Vremenski prozor za prihvatanje: **2 sata**
  - Ako student ne prihvati u roku, nudi se sledećem na listi
  - Student dobija email + push notifikaciju sa dubokim linkom

---

### 2.3 Upravljanje Terminima

#### Pravila Otkazivanja
| Situacija | Akcija | Posledica |
|-----------|--------|-----------|
| Otkazivanje > 24h pre termina | Slobodno, bez penala | — |
| Otkazivanje < 24h pre termina | **Zabranjeno** osim posebnog zahteva | 1 Strike poen |
| Poseban zahtev za kasno otkazivanje | Obrazloženje obavezno (textarea) | Admin/Profesor odlučuje |
| Nepojavljivanje bez otkazivanja | Automatska detekcija (30min posle početka) | 2 Strike poena |

---

### 2.4 Univerzitetska Baza Znanja (Integrisana Pretraga)

#### Google Programmable Search Engine (PSE)
- Integrisani modul za pretragu unutar aplikacije
- **Striktno ograničen** na domene i poddomene fakulteta (primer: `site:fakultet.bg.ac.rs`)
- Rezultati uključuju:
  - HTML stranice (pravilnici, procedure, informacije)
  - **PDF dokumente** indeksirane od strane Google-a
- Podaci se **ne scrap-uju** i ne čuvaju lokalno — sve se vrši live putem Google API-ja

> **Prednost:** Studenti pronalaze zvanične pravilnike, cenovnike i procedure bez napuštanja aplikacije, i bez potrebe za maintainanjem lokalne kopije sadržaja.

---

## 3. Modul za Profesore i Asistente (Staff Portal)

Fokus: automatizacija, smanjenje administrativnog opterećenja, bolja organizacija vremena.

### 3.1 Upravljanje Vremenom (Availability Engine)

#### Dinamički Šabloni (Recurring Slots)
- Profesor kreira **ponavljajuće termine** sa naprednim pravilima:
  - "Svaki utorak od 10:00-12:00"
  - "Svaki utorak, ali **samo tokom zimskog semestra**" (date range ograničenje)
  - "Svaka prva sreda u mesecu"
- Profesor bira **granularnost ponavljanja**: dnevno, nedeljno, mesečno
- Svaki slot ima podešavanje: trajanje (30min / 45min / 60min), maksimalan broj studenata (1-N za grupne), tip (Uživo/Online)

#### Buffer Vreme
- Sistem automatski dodaje **5-10 minuta pauze** između dva zakazana studenta
- Konfigurabilno po profesoru (default: 5 minuta)
- Cilj: sprečavanje gužve ispred kabineta

#### Override i Blackout Datumi
- Profesor jednim klikom **blokira dan/period** zbog: ispita, konferencija, bolovanja, godišnjeg odmora
- **Ako postoje već zakazani termini** u blokiranom periodu:
  - Sistem automatski šalje studentima **notifikaciju o otkazivanju** (sa izvinjenjem)
  - Studenti se automatski stavljaju na prioritetnu listu čekanja
- Ako nema zakazanih termina — blokada se primenjuje tiho

---

### 3.2 Obrada Zahteva

#### Auto-Approve vs. Manual-Approve
- Profesor konfiguriše per-tip:

| Tip Slota | Preporučeno podešavanje | Opis |
|-----------|------------------------|------|
| Recurring (ponavljajući) termini | **Auto-Approve** | Standardni termini se automatski potvrđuju |
| Request (posebni/vanredni) termini | **Manual-Approve** | Profesor ručno pregleda i odobrava/odbija |

- Asistent može imati drugačija podešavanja od profesora

#### Delegiranje Asistentu
- Profesor jednim klikom **prosleđuje zahtev** svom asistentu
- **Uslov:** Asistent mora biti dodeljen istom predmetu kao i zahtev
- Asistent dobija notifikaciju i preuzima zahtev u svoju inbox

#### Šabloni Odgovora (Canned Responses)
- Pri **odbijanju** zahteva, profesor bira brz odgovor umesto kucanja:
  - "Ovo gradivo obrađujemo sledeće nedelje — pokušajte ponovo tada"
  - "Za ovaj problem se obratite asistentu"
  - "Termin je duplo rezervisan, izvinite — izaberite drugi"
  - + Mogućnost dodavanja sopstvenih šablona
- Cilj: smanjiti vreme obrade sa 2 minuta na 10 sekundi

---

### 3.3 Komunikacija i Sinhronizacija

#### In-App Ticket Chat
- Nakon odobrenja termina, automatski se otvara **mini-chat kanal** vezan za taj termin
- Učesnici: student(i) koji su zakazali + profesor (ili asistent ako je delegirano)
- Namena: logistička komunikacija ("Treba li da ponesem odštampan rad?")
- Chat se **automatski zatvara i arhivira** 24h posle završetka termina
- **Nije zamena za email** — limitiran na max 20 poruka po terminu
- Implementovano putem WebSocket-a (FastAPI + Redis Pub/Sub)

#### Privatne CRM Beleške
- Profesor/Asistent vodi interne komentare o svakom studentu:
  - "Ima potencijal za master rad — predložiti temu do kraja semestra"
  - "Upozoren na plagijat 12.03.2025."
  - "Student ima teškoće sa rekurzijom — preporučiti dodatnu literaturu"
- **Vidljive samo osoblju** — student ih nikad ne vidi
- Beleške se čuvaju trajno, asocirane sa parom (profesor, student)

---

## 4. Modul za Studentsku Službu (Admin Panel)

Kontrolni centar za nadzor, intervencije i izveštavanje.

### 4.1 Upravljanje Sistemom

#### Centralni Registar Korisnika
- Puni **CRUD** za sve korisnike (kreiranje, pregled, izmena, deaktivacija)
- **Bulk Import** studenata iz CSV fajla na početku akademske godine:
  - Format: `ime, prezime, email, indeks, smer, godina_upisa`
  - Validacija pre uvoza (duplikati, neispravan email format)
  - Preview pre potvrde uvoza

#### Impersonacija (Log In As)
- Admin može "ući" u nalog bilo kog korisnika radi dijagnoze problema
- **Obavezni Audit Log** za svaku impersonaciju:
  - Timestamp početka i kraja sesije
  - IP adresa admina
  - Lista svih akcija izvršenih u toku impersonacije
- Jasna vizuelna indikacija u UI: crveni baner "ADMIN MODE — Impersonirate [Ime Korisnika]"

#### Globalni Broadcast
- Slanje hitnih obaveštenja za **ciljanu grupu**:
  - Ceo fakultet
  - Specifičan smer (npr. "Softversko inženjerstvo")
  - Specifična godina studija
  - Svi profesori
- **Kanali dostave:**
  - In-app baner (ostaje vidljiv dok admin ne ukloni)
  - Email (sa delay-om od max 5 minuta)
  - Push notifikacija (za PWA korisnike)
- Primer upotrebe: *"Hitno: Zatvaranje zgrade zbog kvara na instalacijama — sve konsultacije danas se otkazuju"*

---

## 5. Sistemski i Quality of Life Dodaci

### 5.1 Strike Sistem (Kazneni Poeni)

Automatizovana penalizacija za neodgovorno ponašanje studenata.

#### Pravila Dodeljeivanja Poena

| Prekršaj | Poeni | Automatizacija |
|----------|-------|----------------|
| Otkazivanje < 12h pre termina | **+1 poen** | Automatski pri otkazivanju |
| Nepojavljivanje bez otkazivanja | **+2 poena** | Automatski 30min posle isteka termina |

#### Posledice

| Broj poena | Posledica |
|-----------|-----------|
| 1-2 poena | Upozorenje (in-app notifikacija + email) |
| 3 poena | **Automatska blokada zakazivanja na 14 dana** |
| 4+ poena | Blokada ostaje; svaki novi prekršaj produžava za 7 dana |

#### Menadžment od strane Admina
- Admin vidi sve studente sa aktivnim kaznenim poenima
- Admin može **skinuti blokadu** ukoliko student donese opravdanje (medicinsko, vanredno)
- Pri skidanju blokade, admin unosi obrazloženje koje se loguje

---

### 5.2 Pametne Notifikacije

#### In-App Centar za Obaveštenja
- Bell ikonika sa brojevim nepročitanih notifikacija
- Dropdown sa listom poslednjih 20 notifikacija
- Sve notifikacije — stranica sa filterima (tip, datum)

#### Automatski Emailovi

| Okidač | Primalac | Vreme slanja |
|--------|---------|-------------|
| Termin potvrđen | Student | Odmah |
| Termin odbijen | Student | Odmah + razlog |
| Podsetnik na termin | Student + Profesor | 24h pre |
| Podsetnik na termin | Student + Profesor | 1h pre |
| Termin otkazan (profesor) | Student | Odmah |
| Slot oslobođen (waitlist) | Sledeći na listi | Odmah (2h prozor) |
| Strike dodat | Student | Odmah |
| Blokada aktivirana | Student | Odmah |

---

### 5.3 PWA (Progressive Web App)

- Instalacija na **iOS i Android uređaje** direktno iz browsera (bez App Store / Play Store)
- Prednosti:
  - Nema proces odobravanja od strane Apple/Google
  - Drastično niži troškovi održavanja
  - Automatski update pri svakom refresh-u
- Offline podrška: Keširanje poslednjih termina i notifikacija za offline pregled (read-only)
- Web Push API za push notifikacije

---

## 6. Planirano za V2

> Ove funkcionalnosti **nisu deo MVP-a** i neće biti razvijane u prvoj fazi. Arhitektura je dizajnirana da ih podrži bez refaktorisanja.

### 6.1 AI RAG Sistem (Pametni Odgovori)
- Prelazak sa Google PSE na **AI asistenta** baziranog na RAG (Retrieval-Augmented Generation) arhitekturi
- AI asistent direktno čita iz dokumenata fakulteta (pravilnici, knjige, beleške)
- Daje konkretne, precizne odgovore umesto liste linkova
- Implementacija: LangChain ili LlamaIndex + pgvector u PostgreSQL
- Model: Claude API ili self-hosted open-source LLM

### 6.2 Analytics Dashboard
- Statistike za profesore: najpopularniji termini, prosečno vreme odgovora, tematske kategorije zahteva
- Statistike za admina: ukupna aktivnost po smerovima, no-show stopa

---

*Dokument je deo `docs/` foldera projekta i služi kao jedini source of truth za poslovne zahteve.*
