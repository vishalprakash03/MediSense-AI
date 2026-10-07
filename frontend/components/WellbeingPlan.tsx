type Recommendations = {
  today?: string[];
  food?: string[];
  watchouts?: string[];
  condition_guidance?: ConditionGuidance[];
};

type ConditionGuidance = {
  condition: string;
  lifestyle: string[];
  food: string[];
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
      {recommendations.condition_guidance?.length ? (
        <div className="border-t border-slate-100 p-5">
          <div className="mb-4">
            <p className="text-sm font-semibold text-slate-800">Guidance for each screening</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">These suggestions support health; they do not confirm a condition or replace a personal care plan.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {recommendations.condition_guidance.map((guidance) => (
              <article key={guidance.condition} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                <h3 className="font-semibold text-slate-800">{guidance.condition}</h3>
                <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-brand-700">Lifestyle</p>
                <List items={guidance.lifestyle} />
                <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-amber-800">Food</p>
                <List items={guidance.food} />
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
