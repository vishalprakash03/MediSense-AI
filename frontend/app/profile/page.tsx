"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import PageVisual from "@/components/PageVisual";
import { deleteAccount, getToken, getProfile, logout, updateProfile } from "@/services/api";

export default function ProfilePage() {
  const router = useRouter();
  const [account, setAccount] = useState<any>(null);
  const [profile, setProfile] = useState<any>({});
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    getProfile().then((res) => {
      setAccount(res.data);
      setProfile(res.data.profile || {});
    });
  }, [router]);

  function update(field: string, value: any) {
    setProfile((p: any) => ({ ...p, [field]: value }));
    setSaved(false);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await updateProfile(profile);
      setSaved(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "We couldn’t save your profile. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteAccount() {
    const confirmed = window.confirm(
      "Delete your account and all stored health data? This cannot be undone."
    );
    if (!confirmed) return;

    setDeleting(true);
    setError("");
    try {
      await deleteAccount();
      logout();
      router.replace("/register");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "We couldn’t delete your account. Please try again.");
      setDeleting(false);
    }
  }

  return (
    <div className="app-shell flex">
      <Sidebar />
      <main className="app-main visual-page visual-page-profile flex-1 p-5 pt-20 md:p-8">
        <section className="project-page-hero mb-6 overflow-hidden rounded-3xl bg-gradient-to-r from-teal-800 via-emerald-700 to-cyan-600 px-6 py-7 text-white shadow-lg shadow-emerald-950/10">
          <div className="relative z-10 max-w-xl sm:pr-36">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-100">Your private space</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight">Profile</h1>
            <p className="mt-2 text-sm leading-6 text-emerald-50">Manage your account and the health details that support a more personal screening experience.</p>
          </div>
          <PageVisual visual="profile" className="project-hero-visual project-hero-visual-compact" />
        </section>

        {account && (
          <div className="card mb-6">
            <p className="text-sm text-gray-500">Name</p>
            <p className="font-medium text-gray-800 mb-3">{account.name}</p>
            <p className="text-sm text-gray-500">Email</p>
            <p className="font-medium text-gray-800 mb-3">{account.email}</p>
            <p className="text-sm text-gray-500">Age / Gender</p>
            <p className="font-medium text-gray-800">{account.age} · {account.gender}</p>
          </div>
        )}

        <form onSubmit={handleSave} className="card space-y-4">
          <h2 className="font-semibold text-gray-800">Health Profile</h2>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Height (cm)" value={profile.height_cm} onChange={(v: any) => update("height_cm", v)} />
            <Field label="Weight (kg)" value={profile.weight_kg} onChange={(v: any) => update("weight_kg", v)} />
            <Field label="Weekly physical activity (hrs)" value={profile.physical_activity_hours} onChange={(v: any) => update("physical_activity_hours", v)} />
            <Field label="Average sleep (hrs)" value={profile.sleep_hours} onChange={(v: any) => update("sleep_hours", v)} />
          </div>

          <div>
            <label className="text-sm text-gray-600">Smoking status</label>
            <select className="input-field mt-1" value={profile.smoking_status || ""}
              onChange={(e) => update("smoking_status", e.target.value)}>
              <option value="">Select…</option>
              <option value="never">Never smoked</option>
              <option value="former">Former smoker</option>
              <option value="current">Current smoker</option>
            </select>
          </div>

          <div>
            <label className="text-sm text-gray-600">Dietary habits</label>
            <input className="input-field mt-1" value={profile.dietary_habits || ""}
              onChange={(e) => update("dietary_habits", e.target.value)} placeholder="e.g. Balanced, high-protein, vegetarian" />
          </div>

          <div>
            <label className="text-sm text-gray-600">Stress level (1–10)</label>
            <input type="number" min={1} max={10} className="input-field mt-1"
              value={profile.stress_level || ""} onChange={(e) => update("stress_level", parseInt(e.target.value))} />
          </div>

          <button className="btn-primary" disabled={saving}>
            {saving ? "Saving…" : "Save Profile"}
          </button>
          {saved && <p className="text-sm text-green-600">Profile updated.</p>}
        </form>

        <section className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-6">
          <h2 className="font-semibold text-red-900">Delete account and health data</h2>
          <p className="mt-1 text-sm text-red-800">
            This permanently removes your account, health profile, measurements, assessments, and chat history.
          </p>
          <button
            type="button"
            onClick={handleDeleteAccount}
            disabled={deleting}
            className="mt-4 rounded-xl bg-red-600 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {deleting ? "Deleting…" : "Delete my account"}
          </button>
        </section>
        {error && <p className="mt-4 text-sm text-red-600" role="alert">{error}</p>}
      </main>
    </div>
  );
}

function Field({ label, value, onChange }: { label: string; value: any; onChange: (v: any) => void }) {
  return (
    <div>
      <label className="text-sm text-gray-600">{label}</label>
      <input
        type="number" step="0.1" className="input-field mt-1"
        value={value ?? ""} onChange={(e) => onChange(parseFloat(e.target.value))}
      />
    </div>
  );
}
