"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Sidebar from "@/components/Sidebar";
import PageVisual from "@/components/PageVisual";
import { getToken, listSymptomCheckIns } from "@/services/api";

type CheckIn = {
  _id: string;
  symptoms?: string[];
  notes?: string;
  recorded_at: string;
};

type SafetyAlert = {
  level: "urgent" | "follow_up";
  title: string;
  message: string;
};

function localDateKey(value: string) {
  const date = new Date(value);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function dateLabel(value: string) {
  return new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function fullDateLabel(value: string) {
  return new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function SymptomsPage() {
  const router = useRouter();
  const [checkins, setCheckins] = useState<CheckIn[]>([]);
  const [alerts, setAlerts] = useState<SafetyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    listSymptomCheckIns()
      .then((response) => {
        setCheckins(response.data.checkins || []);
        setAlerts(response.data.alerts || []);
      })
      .catch(() => setError("We could not load your symptom history. Please try again."))
      .finally(() => setLoading(false));
  }, [router]);

  const chartData = useMemo(() => {
    const counts = new Map<string, number>();
    checkins.forEach((checkin) => {
      const key = localDateKey(checkin.recorded_at);
      counts.set(key, (counts.get(key) || 0) + (checkin.symptoms?.length || 0));
    });

    const today = new Date();
    return Array.from({ length: 30 }, (_, offset) => {
      const day = new Date(today);
      day.setHours(0, 0, 0, 0);
      day.setDate(today.getDate() - (29 - offset));
      const key = localDateKey(day.toISOString());
      return {
        date: day.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
        symptomCount: counts.get(key) || 0,
      };
    });
  }, [checkins]);

  return (
    <div className="app-shell flex">
      <Sidebar />
      <main className="app-main visual-page visual-page-symptoms flex-1 space-y-6 p-5 pt-20 md:p-8">
        <section className="project-page-hero overflow-hidden rounded-3xl bg-gradient-to-r from-violet-700 via-indigo-700 to-cyan-700 px-6 py-7 text-white shadow-sm">
          <div className="relative z-10 max-w-2xl md:pr-44">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-violet-100">Personal monitoring</p>
            <h1 className="mt-2 text-3xl font-semibold">Symptoms & notes</h1>
            <p className="mt-2 text-sm leading-6 text-violet-50">Review what you recorded, notice recurring patterns, and prepare clearer information for a healthcare appointment.</p>
          </div>
          <PageVisual visual="symptoms" className="project-hero-visual" />
        </section>

        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <strong>This page is not a diagnosis or emergency service.</strong> If you have new or severe chest pain, trouble breathing, fainting, or stroke-like symptoms, seek urgent medical care now.
        </section>

        {loading && <p className="text-sm text-slate-500">Loading symptom history…</p>}
        {error && <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}

        {!loading && !error && (
          <>
            {alerts.length > 0 && (
              <section className="space-y-3" aria-label="Symptom safety notices">
                {alerts.map((alert, index) => (
                  <div key={`${alert.title}-${index}`} className={`rounded-2xl border p-4 ${alert.level === "urgent" ? "border-red-200 bg-red-50 text-red-900" : "border-amber-200 bg-amber-50 text-amber-900"}`}>
                    <h2 className="font-semibold">{alert.title}</h2>
                    <p className="mt-1 text-sm leading-6">{alert.message}</p>
                  </div>
                ))}
              </section>
            )}

            <section className="card">
              <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-800">Last 30 days</h2>
                  <p className="text-sm text-slate-500">Number of symptom entries recorded each day.</p>
                </div>
                <p className="text-sm font-medium text-violet-700">{checkins.length} saved check-in{checkins.length === 1 ? "" : "s"}</p>
              </div>
              <div className="mt-5 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip formatter={(value) => [value, "Symptoms logged"]} />
                    <Bar dataKey="symptomCount" name="Symptoms logged" fill="#7c3aed" radius={[5, 5, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="card">
              <h2 className="text-lg font-semibold text-slate-800">Check-in timeline</h2>
              <p className="mt-1 text-sm text-slate-500">Showing up to your latest 90 records.</p>
              {checkins.length === 0 ? (
                <p className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">No check-ins yet. Use “Check in now” on the Dashboard to start your private symptom record.</p>
              ) : (
                <div className="mt-5 space-y-3">
                  {[...checkins].reverse().map((checkin) => (
                    <article key={checkin._id} className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                        <h3 className="font-semibold text-slate-800">{dateLabel(checkin.recorded_at)}</h3>
                        <time className="text-xs text-slate-500" dateTime={checkin.recorded_at}>{fullDateLabel(checkin.recorded_at)}</time>
                      </div>
                      {checkin.symptoms && checkin.symptoms.length > 0 ? (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {checkin.symptoms.map((symptom, index) => <span key={`${symptom}-${index}`} className="rounded-full bg-violet-100 px-3 py-1 text-sm text-violet-800">{symptom}</span>)}
                        </div>
                      ) : <p className="mt-3 text-sm text-slate-500">No symptoms were recorded.</p>}
                      {checkin.notes && <p className="mt-3 border-l-2 border-violet-200 pl-3 text-sm leading-6 text-slate-700">{checkin.notes}</p>}
                    </article>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
