export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 bg-gradient-to-b from-slate-50 to-slate-100">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          Studentska Platforma
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Platforma za upravljanje univerzitetskim konsultacijama i komunikacijom
        </p>
        <div className="space-x-4">
          <a
            href="/api/v1/auth/sso/redirect"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Prijavi se
          </a>
        </div>
      </div>
      
      <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl">
        <div className="p-6 bg-white rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Za Studente</h3>
          <p className="text-gray-600">
            Pretraži profesore i zakazuj konsultacije brzo i lako
          </p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Za Profesore</h3>
          <p className="text-gray-600">
            Upravljaj vremenom dostupnosti i komunikacijom sa studentima
          </p>
        </div>
        <div className="p-6 bg-white rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Za Administratore</h3>
          <p className="text-gray-600">
            Nadzor sistema i upravljanje korisnicima
          </p>
        </div>
      </div>
    </div>
  )
}
