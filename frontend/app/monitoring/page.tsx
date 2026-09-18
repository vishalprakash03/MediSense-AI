"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import Sidebar from "@/components/Sidebar";
import { getToken, addMeasurement, listMeasurements } from "@/services/api";

export default function MonitoringPage() {
  const router = useRouter();
  const [measurements, setMeasurements] = useState<any[]>([]);
  const [form, setForm] = useState({
    blood_pressure_systolic: "", blood_pressure_diastolic: "",
    heart_rate: "", temperature: "", weight_kg: "",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    refresh();
  }, [router]);

  async function refresh() {
    const res = await listMeasurements();
    setMeasurements(res.data.measurements);
  }

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload: any = {};
      Object.entries(form).forEach(([k, v]) => {
        if (v !== "") payload[k] = parseFloat(v as string);
      });
      await addMeasurement(payload);
      setForm({ blood_pressure_systolic: "", blood_pressure_diastolic: "", heart_rate: "", temperature: "", weight_kg: "" });
      await refresh();
    } finally {
      setSaving(false);
    }
  }

  const chartData = measurements.map((m) => ({
    date: new Date(m.recorded_at).toLocaleDateString(),
    systolic: m.blood_pressure_systolic,
    heartRate: m.heart_rate,
    weight: m.weight_kg,
    temperature: m.temperature,
  }));

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 space-y-6 p-5 pt-20 md:p-8">
        <div>
          <h1 className="text-2xl font-semibold text-gray-800">Health Monitoring</h1>
          <p className="text-gray-500 text-sm mt-1">Log measurements and track trends over time.</p>
        </div>

        <div className="card">
          <h2 className="font-semibold text-gray-800 mb-4">Update Health Parameters</h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <input placeholder="Systolic BP" className="input-field" value={form.blood_pressure_systolic}
              onChange={(e) => update("blood_pressure_systolic", e.target.value)} />
            <input placeholder="Diastolic BP" className="input-field" value={form.blood_pressure_diastolic}
              onChange={(e) => update("blood_pressure_diastolic", e.target.value)} />
            <input placeholder="Heart Rate" className="input-field" value={form.heart_rate}
              onChange={(e) => update("heart_rate", e.target.value)} />
            <input placeholder="Temp (°C)" className="input-field" value={form.temperature}
              onChange={(e) => update("temperature", e.target.value)} />
            <input placeholder="Weight (kg)" className="input-field" value={form.weight_kg}
              onChange={(e) => update("weight_kg", e.target.value)} />
            <button className="btn-primary col-span-2 md:col-span-5" disabled={saving}>
              {saving ? "Saving…" : "Save Measurement"}
            </button>
          </form>
        </div>

        {measurements.length === 0 ? (
          <p className="text-sm text-gray-500">No measurements logged yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <ChartCard title="Blood Pressure (Systolic) Trend" dataKey="systolic" data={chartData} color="#0f9d75" />
            <ChartCard title="Heart Rate Trend" dataKey="heartRate" data={chartData} color="#e07a3f" />
            <ChartCard title="Weight Trend" dataKey="weight" data={chartData} color="#3f7de0" />
            <ChartCard title="Temperature Trend" dataKey="temperature" data={chartData} color="#c23f6b" />
          </div>
        )}
      </main>
    </div>
  );
}

function ChartCard({ title, dataKey, data, color }: { title: string; dataKey: string; data: any[]; color: string }) {
  return (
    <div className="card">
      <h3 className="font-semibold text-gray-700 mb-3 text-sm">{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} domain={["auto", "auto"]} />
          <Tooltip />
          <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} connectNulls dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
