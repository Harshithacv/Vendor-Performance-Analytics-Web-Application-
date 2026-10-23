import { BarChart3, Boxes, Truck } from 'lucide-react'

const features = [
  {
    icon: BarChart3,
    title: 'Performance Analytics',
    description: 'Review vendor performance and business metrics.'
  },
  {
    icon: Truck,
    title: 'Vendor Management',
    description: 'Organize vendor information and performance records.'
  },
  {
    icon: Boxes,
    title: 'Inventory Insights',
    description: 'Prepare to monitor inventory and stock movement.'
  }
]

export default function App() {
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-12 text-slate-100 sm:px-10">
      <div className="mx-auto max-w-6xl">
        <header className="mb-12">
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">
            Analytics workspace
          </p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-5xl">
            Vendor Performance Analytics
          </h1>
          <p className="mt-4 max-w-2xl text-slate-400">
            Your frontend foundation is ready. Build insights into vendor
            performance, purchasing, and inventory from one workspace.
          </p>
        </header>

        <section className="grid gap-5 md:grid-cols-3">
          {features.map(({ icon: Icon, title, description }) => (
            <article
              key={title}
              className="rounded-2xl border border-slate-800 bg-slate-900 p-6"
            >
              <div className="mb-5 inline-flex rounded-xl bg-blue-500/10 p-3 text-blue-400">
                <Icon size={24} />
              </div>
              <h2 className="text-lg font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                {description}
              </p>
            </article>
          ))}
        </section>

        <footer className="mt-12 border-t border-slate-800 pt-6 text-sm text-slate-500">
          React · Vite · Tailwind CSS
        </footer>
      </div>
    </main>
  )
}
