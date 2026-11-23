"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getSupabaseClient } from "@/lib/supabase";

export default function AuthPage() {
  const supabase = useMemo(() => getSupabaseClient(), []);
  const router = useRouter();
  const [mode, setMode] = useState<"sign-in" | "sign-up">("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!supabase) {
      setError("Authentication is not configured for this deployment yet.");
      return;
    }
    setBusy(true);
    try {
      if (mode === "sign-in") {
        const { error: authError } = await supabase.auth.signInWithPassword({ email, password });
        if (authError) throw authError;
        router.replace("/memories");
        router.refresh();
      } else {
        const { data, error: authError } = await supabase.auth.signUp({
          email,
          password,
          options: { emailRedirectTo: window.location.origin + "/memories" },
        });
        if (authError) throw authError;
        if (data.session) {
          router.replace("/memories");
          router.refresh();
        } else {
          setMessage("Account created. Check your email to confirm the address, then sign in.");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white flex items-center justify-center px-4 py-12">
      <section className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-8 shadow-2xl">
        <Link href="/" className="text-sm text-cyan-300 hover:text-cyan-200">← Back to NomadsAI</Link>
        <h1 className="mt-6 text-3xl font-semibold">Your NomadsAI account</h1>
        <p className="mt-2 text-sm text-slate-400">Sign in to save and manage your private travel memories.</p>
        <div className="mt-6 grid grid-cols-2 rounded-lg bg-slate-800 p-1">
          <button type="button" onClick={() => { setMode("sign-in"); setError(""); setMessage(""); }}
            className={"rounded-md px-3 py-2 text-sm " + (mode === "sign-in" ? "bg-cyan-400 text-slate-950 font-semibold" : "text-slate-300")}>Sign in</button>
          <button type="button" onClick={() => { setMode("sign-up"); setError(""); setMessage(""); }}
            className={"rounded-md px-3 py-2 text-sm " + (mode === "sign-up" ? "bg-cyan-400 text-slate-950 font-semibold" : "text-slate-300")}>Create account</button>
        </div>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block text-sm text-slate-300">Email
            <input type="email" required autoComplete="email" value={email} onChange={event => setEmail(event.target.value)}
              className="mt-2 w-full rounded-lg border border-white/10 bg-slate-800 px-4 py-3 text-white outline-none focus:border-cyan-400" />
          </label>
          <label className="block text-sm text-slate-300">Password
            <input type="password" required minLength={8} autoComplete={mode === "sign-in" ? "current-password" : "new-password"}
              value={password} onChange={event => setPassword(event.target.value)}
              className="mt-2 w-full rounded-lg border border-white/10 bg-slate-800 px-4 py-3 text-white outline-none focus:border-cyan-400" />
            {mode === "sign-up" && <span className="mt-1 block text-xs text-slate-500">Use at least 8 characters.</span>}
          </label>
          {error && <p role="alert" className="rounded-lg bg-red-950/60 p-3 text-sm text-red-300">{error}</p>}
          {message && <p role="status" className="rounded-lg bg-emerald-950/60 p-3 text-sm text-emerald-300">{message}</p>}
          <button type="submit" disabled={busy || !supabase}
            className="w-full rounded-lg bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50">
            {busy ? "Please wait…" : mode === "sign-in" ? "Sign in" : "Create account"}
          </button>
          {!supabase && <p className="text-xs text-amber-300">Deployment configuration is pending. Account services will become available after the Supabase environment variables are added.</p>}
        </form>
      </section>
    </main>
  );
}
