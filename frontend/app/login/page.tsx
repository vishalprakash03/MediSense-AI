"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { loginUser, startSession, saveUser } from "@/services/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await loginUser({ email, password });
      startSession();
      saveUser(res.data.user);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="medical-auth-page flex items-center justify-center px-4">
      <div className="card medical-auth-card w-full max-w-md">
        <div className="text-center mb-6">
          <div className="mx-auto mb-3 grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-brand-100 to-cyan-100 text-3xl shadow-sm">🩺</div>
          <h1 className="text-xl font-semibold text-brand-700">MediSense AI</h1>
          <p className="text-sm text-gray-600 mt-1">Your private space for health screening and monitoring</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm text-gray-600">Email</label>
            <input
              type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field mt-1" placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="text-sm text-gray-600">Password</label>
            <input
              type="password" required value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field mt-1" placeholder="••••••••"
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        <p className="text-sm text-gray-500 text-center mt-6">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-brand-600 font-medium">Create one</Link>
        </p>
      </div>
    </div>
  );
}
