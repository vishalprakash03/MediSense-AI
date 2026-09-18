"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import Disclaimer from "@/components/Disclaimer";
import RiskCard from "@/components/RiskCard";
import SymptomReminder from "@/components/SymptomReminder";
import { getToken, getUser, getLatest, listMeasurements } from "@/services/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [latest, setLatest] = useState<any>(null);
  const [measurements, setMeasurements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setUser(getUser());

    Promise.all([getLatest(), listMeasurements()])
      .then(([latestRes, measRes]) => {
        setLatest(latestRes.data.latest);
        setMeasurements(measRes.data.measurements.slice(-5).reverse());
      })
      .finally(() => setLoading(false));
  }, [router]);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 space-y-6 p-5 pt-20 md:p-8">
        <section className="overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-brand-800 to-brand-500 px-6 py-8 text-white shadow-xl shadow-brand-900/10">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-100">Your health space</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Welcome back{user?.name ? `, ${user.name}` : ""}.</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-brand-50">Check in, keep your measurements organized, and use your results as a conversation starter with a healthcare professional.</p>
        </section>

        <Disclaimer />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href="/assistant" className="group card border-brand-100 hover:-translate-y-0.5 hover:shadow-md transition-all cursor-pointer">
            <div className="mb-3 inline-flex rounded-2xl bg-brand-50 p-3 text-2xl">💬</div>
            <h3 className="font-semibold text-gray-800">Health assessment <span className="text-brand-600 transition-transform group-hover:translate-x-0.5 inline-block">→</span></h3>
            <p className="mt-1 text-sm text-gray-500">Answer guided questions and review your screening results.</p>
          </Link>
          <Link href="/monitoring" className="group card border-blue-100 hover:-translate-y-0.5 hover:shadow-md transition-all cursor-pointer">
            <div className="mb-3 inline-flex rounded-2xl bg-blue-50 p-3 text-2xl">📈</div>
            <h3 className="font-semibold text-gray-800">Track measurements <span className="text-brand-600 transition-transform group-hover:translate-x-0.5 inline-block">→</span></h3>
            <p className="mt-1 text-sm text-gray-500">Log blood pressure, weight, heart rate, and more.</p>
          </Link>
          <Link href="/history" className="group card border-violet-100 hover:-translate-y-0.5 hover:shadow-md transition-all cursor-pointer">
            <div className="mb-3 inline-flex rounded-2xl bg-violet-50 p-3 text-2xl">🗂️</div>
            <h3 className="font-semibold text-gray-800">Review history <span className="text-brand-600 transition-transform group-hover:translate-x-0.5 inline-block">→</span></h3>
            <p className="mt-1 text-sm text-gray-500">Compare your past health assessments over time.</p>
          </Link>
        </div>

        <SymptomReminder />

        <div>
          <h2 className="font-semibold text-gray-800 mb-3">Latest Health Assessment</h2>
          {loading ? (
            <p className="text-sm text-gray-400">Loading…</p>
          ) : !latest ? (
            <div className="card text-sm text-gray-500">
              No assessments yet. <Link href="/assistant" className="text-brand-600 font-medium">Talk to MediSense AI</Link> to get your first health-risk overview.
            </div>
          ) : (
            <div className="space-y-3">
              <div className="card flex items-center justify-between">
                <span className="text-sm text-gray-500">
                  Overall risk (as of {new Date(latest.created_at).toLocaleDateString()})
                </span>
                <span className={`text-sm font-semibold px-3 py-1 rounded-full ${latest.overall_risk === "High" ? "risk-high" :
                    latest.overall_risk === "Moderate" ? "risk-moderate" :
                    latest.overall_risk === "Low" ? "risk-low" : "bg-gray-100 text-gray-600"
                  }`}>
                  {latest.overall_risk}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {latest.predicted_conditions?.map((p: any, i: number) => (
                  <RiskCard key={i} prediction={p} />
                ))}
              </div>
            </div>
          )}
        </div>

        {measurements.length > 0 && (
          <div>
            <h2 className="font-semibold text-gray-800 mb-3">Recent Health Measurements</h2>
            <div className="card overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-gray-400 border-b">
                  <tr>
                    <th className="py-2 pr-4">Date</th>
                    <th className="py-2 pr-4">Blood Pressure</th>
                    <th className="py-2 pr-4">Heart Rate</th>
                    <th className="py-2 pr-4">Weight (kg)</th>
                  </tr>
                </thead>
                <tbody>
                  {measurements.map((m, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-2 pr-4">{new Date(m.recorded_at).toLocaleDateString()}</td>
                      <td className="py-2 pr-4">
                        {m.blood_pressure_systolic ? `${m.blood_pressure_systolic}/${m.blood_pressure_diastolic ?? "-"}` : "—"}
                      </td>
                      <td className="py-2 pr-4">{m.heart_rate ?? "—"}</td>
                      <td className="py-2 pr-4">{m.weight_kg ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
