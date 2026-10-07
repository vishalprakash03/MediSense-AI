"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import RiskCard from "@/components/RiskCard";
import PageVisual from "@/components/PageVisual";
import { getToken, getHistory } from "@/services/api";

export default function HistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<any[]>([]);
  const [selected, setSelected] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    getHistory().then((res) => {
      const items = (res.data.history || []).filter((h: any) => h.overall_risk !== "Unassessed");
      setHistory(items);
      setSelected(items[0] || null);
    }).finally(() => setLoading(false));
  }, [router]);

  return (
    <div className="app-shell flex">
      <Sidebar />
      <main className="app-main visual-page visual-page-history flex-1 space-y-6 p-5 pt-20 md:p-8">
        <section className="project-page-hero overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-800 via-blue-700 to-cyan-600 px-6 py-7 text-white shadow-lg shadow-blue-950/10">
          <div className="relative z-10 max-w-2xl md:pr-44">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-100">Your assessment timeline</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight">Prediction history</h1>
            <p className="mt-2 text-sm leading-6 text-indigo-50">Review previous health assessments and use the trend as a helpful discussion point with your healthcare professional.</p>
          </div>
          <PageVisual visual="history" className="project-hero-visual" />
        </section>

        {loading ? (
          <p className="text-sm text-gray-400">Loading…</p>
        ) : history.length === 0 ? (
          <div className="card text-sm text-gray-500">
            No assessments yet. Talk to MediSense AI to run your first one.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="md:col-span-1 space-y-2">
              {history.map((h) => (
                <button
                  key={h.assessment_id}
                  onClick={() => setSelected(h)}
                  className={`w-full text-left card !p-3 ${
                    selected?.assessment_id === h.assessment_id ? "ring-2 ring-brand-500" : ""
                  }`}
                >
                  <p className="text-sm font-medium text-gray-700">
                    {new Date(h.created_at).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-gray-500">{h.overall_risk} overall risk</p>
                </button>
              ))}
            </div>

            <div className="md:col-span-3 space-y-4">
              {selected && (
                <>
                  <div className="card flex items-center justify-between">
                    <span className="text-sm text-gray-500">
                      Assessment from {new Date(selected.created_at).toLocaleString()}
                    </span>
                    <span className={`text-sm font-semibold px-3 py-1 rounded-full ${
                      selected.overall_risk === "High" ? "risk-high" :
                      selected.overall_risk === "Moderate" ? "risk-moderate" :
                      selected.overall_risk === "Low" ? "risk-low" : "bg-gray-100 text-gray-600"
                    }`}>
                      {selected.overall_risk}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selected.predicted_conditions?.map((p: any, i: number) => (
                      <RiskCard key={i} prediction={p} />
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
