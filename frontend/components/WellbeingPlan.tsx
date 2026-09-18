type Recommendations = {
  today?: string[];
  food?: string[];
  watchouts?: string[];
};

function List({ items }: { items?: string[] }) {
  if (!items?.length) return null;
  return (
    <ul className="mt-3 space-y-2 text-sm leading-5 text-slate-600">
      {items.map((item) => <li key={item} className="flex gap-2"><span className="text-brand-600">•</span><span>{item}</span></li>)}
    </ul>
  );
}

export default function WellbeingPlan({ recommendations }: { recommendations?: Recommendations }) {
  if (!recommendations) return null;
  return (
    <section className="overflow-hidden rounded-3xl border border-brand-100 bg-white shadow-sm">
      <div className="bg-gradient-to-r from-brand-700 to-brand-500 px-6 py-5 text-white">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-100">Your next steps</p>
        <h2 className="mt-1 text-xl font-semibold">A practical wellbeing plan</h2>
        <p className="mt-1 text-sm text-brand-50">General guidance only—not medical treatment or a diagnosis.</p>
      </div>
      <div className="grid gap-5 p-5 md:grid-cols-2">
        <div className="rounded-2xl bg-brand-50 p-4">
          <p className="text-sm font-semibold text-brand-800">Today & this week</p>
          <List items={recommendations.today} />
        </div>
        <div className="rounded-2xl bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-900">Food choices to support health</p>
          <List items={recommendations.food} />
        </div>
      </div>
      {recommendations.watchouts?.length ? (
        <div className="border-t border-red-100 bg-red-50 px-5 py-4">
          <p className="text-sm font-semibold text-red-900">When to seek care</p>
          <List items={recommendations.watchouts} />
        </div>
      ) : null}
    </section>
  );
}
