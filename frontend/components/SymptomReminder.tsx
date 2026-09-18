"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { addSymptomCheckIn, getLatestSymptomCheckIn } from "@/services/api";

const REMINDER_TIME_KEY = "medisense_symptom_reminder_time";
const REMINDER_SENT_KEY = "medisense_symptom_reminder_sent";

function dateKey() {
  return new Date().toISOString().slice(0, 10);
}

export default function SymptomReminder() {
  const [time, setTime] = useState("19:00");
  const [enabled, setEnabled] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [symptoms, setSymptoms] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [latest, setLatest] = useState<any>(null);

  useEffect(() => {
    const savedTime = window.localStorage.getItem(REMINDER_TIME_KEY);
    if (savedTime) {
      setTime(savedTime);
      setEnabled(true);
    }
    getLatestSymptomCheckIn().then((res) => setLatest(res.data.latest)).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!enabled) return;
    const maybeNotify = () => {
      const now = new Date();
      const nowTime = now.toTimeString().slice(0, 5);
      if (nowTime < time || window.localStorage.getItem(REMINDER_SENT_KEY) === dateKey()) return;
      window.localStorage.setItem(REMINDER_SENT_KEY, dateKey());
      setShowForm(true);
      if ("Notification" in window && Notification.permission === "granted") {
        new Notification("MediSense AI", { body: "How are your symptoms today? Take a short check-in." });
      }
    };
    maybeNotify();
    const timer = window.setInterval(maybeNotify, 60_000);
    return () => window.clearInterval(timer);
  }, [enabled, time]);

  async function enableReminder() {
    window.localStorage.setItem(REMINDER_TIME_KEY, time);
    setEnabled(true);
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }
  }

  async function saveCheckIn(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const parsedSymptoms = symptoms.split(",").map((item) => item.trim()).filter(Boolean);
      await addSymptomCheckIn({ symptoms: parsedSymptoms, notes: notes.trim() || undefined });
      setLatest({ symptoms: parsedSymptoms, recorded_at: new Date().toISOString() });
      setSymptoms("");
      setNotes("");
      setShowForm(false);
      setMessage("Today’s symptom check-in is saved.");
    } catch {
      setMessage("We couldn’t save your check-in. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  const checkedInToday = latest?.recorded_at?.slice(0, 10) === dateKey();
  return (
    <section className="rounded-3xl border border-violet-100 bg-gradient-to-br from-violet-50 to-white p-5 shadow-sm">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-600">Daily check-in</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-800">Keep a simple symptom record</h2>
          <p className="mt-1 max-w-xl text-sm text-slate-600">A private daily note can help you spot changes to discuss with a clinician.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/symptoms" className="rounded-xl border border-violet-200 bg-white px-4 py-2.5 text-sm font-medium text-violet-700 hover:bg-violet-50">View history</Link>
          <button onClick={() => setShowForm(true)} className="btn-primary whitespace-nowrap">{checkedInToday ? "Update check-in" : "Check in now"}</button>
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3 rounded-2xl bg-white/80 p-3 sm:flex-row sm:items-center">
        <label className="text-sm font-medium text-slate-700" htmlFor="reminder-time">Daily reminder</label>
        <input id="reminder-time" type="time" value={time} onChange={(e) => setTime(e.target.value)} className="rounded-lg border border-slate-200 px-2 py-1.5 text-sm" />
        <button type="button" onClick={enableReminder} className="rounded-lg border border-violet-200 px-3 py-1.5 text-sm font-medium text-violet-700 hover:bg-violet-50">
          {enabled ? "Reminder on" : "Turn on reminder"}
        </button>
        <span className="text-xs text-slate-500">Browser alert works while this app is open.</span>
      </div>

      {showForm && (
        <form onSubmit={saveCheckIn} className="mt-4 space-y-3 rounded-2xl border border-violet-100 bg-white p-4">
          <label className="block text-sm font-medium text-slate-700">Symptoms today <span className="font-normal text-slate-400">(comma-separated; leave blank if none)</span>
            <input value={symptoms} onChange={(e) => setSymptoms(e.target.value)} className="input-field mt-1" placeholder="e.g. headache, tiredness" />
          </label>
          <label className="block text-sm font-medium text-slate-700">Notes <span className="font-normal text-slate-400">(optional)</span>
            <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="input-field mt-1 min-h-20" maxLength={1000} placeholder="Anything you want to remember for your next appointment" />
          </label>
          <div className="flex gap-2"><button disabled={saving} className="btn-primary">{saving ? "Saving…" : "Save check-in"}</button><button type="button" onClick={() => setShowForm(false)} className="rounded-xl px-4 py-2 text-sm text-slate-600">Cancel</button></div>
        </form>
      )}
      {message && <p className="mt-3 text-sm text-violet-700" role="status">{message}</p>}
    </section>
  );
}
