"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { registerUser, startSession, saveUser } from "@/services/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", age: "", gender: "female", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await registerUser({ ...form, age: parseInt(form.age, 10) });
      startSession();
      saveUser(res.data.user);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="medical-auth-page flex items-center justify-center px-4 py-10">
      <div className="card medical-auth-card w-full max-w-md">
        <div className="text-center mb-6">
          <div className="mx-auto mb-3 grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-brand-100 to-cyan-100 text-3xl shadow-sm">🩺</div>
          <h1 className="text-xl font-semibold text-brand-700">Create your account</h1>
          <p className="text-sm text-gray-600 mt-1">Start your private health-monitoring journey</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-gray-600">Full name</label>
            <input required className="input-field mt-1" value={form.name}
              onChange={(e) => update("name", e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm text-gray-600">Age</label>
              <input required type="number" min={0} max={120} className="input-field mt-1"
                value={form.age} onChange={(e) => update("age", e.target.value)} />
            </div>
            <div>
              <label className="text-sm text-gray-600">Gender</label>
              <select className="input-field mt-1" value={form.gender}
                onChange={(e) => update("gender", e.target.value)}>
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-sm text-gray-600">Email</label>
            <input required type="email" className="input-field mt-1" value={form.email}
              onChange={(e) => update("email", e.target.value)} />
          </div>
          <div>
            <label className="text-sm text-gray-600">Password</label>
            <input required type="password" minLength={8} className="input-field mt-1"
              value={form.password} onChange={(e) => update("password", e.target.value)} />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Creating account…" : "Create Account"}
          </button>
        </form>

        <p className="text-sm text-gray-500 text-center mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-brand-600 font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
