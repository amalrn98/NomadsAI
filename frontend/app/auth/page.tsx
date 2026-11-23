"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Compass, Eye, EyeOff, Globe2, MapPin, Sparkles } from "lucide-react";
import { getSupabaseClient } from "@/lib/supabase";

type Mode = "sign-in" | "sign-up";

export default function AuthPage() {
  const supabase = useMemo(() => getSupabaseClient(), []);
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("sign-in");
  const [recovery, setRecovery] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("mode") === "sign-up") setMode("sign-up");
    if (window.location.hash.includes("type=recovery")) setRecovery(true);
  }, []);

  function changeMode(next: Mode) {
    setMode(next);
    setRecovery(false);
    setError("");
    setMessage("");
    window.history.replaceState(null, "", next === "sign-up" ? "/auth?mode=sign-up" : "/auth");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!supabase) {
      setError("Account services are not configured for this deployment yet.");
      return;
    }
    setBusy(true);
    try {
      if (recovery) {
        const { error: authError } = await supabase.auth.updateUser({ password });
        if (authError) throw authError;
        setRecovery(false);
        setPassword("");
        setMessage("Password updated. Sign in with your new password.");
        window.history.replaceState(null, "", "/auth");
      } else if (mode === "sign-in") {
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
          setMessage("Your account is created. Check your inbox for the verification email, then sign in.");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function sendPasswordReset() {
    setError("");
    setMessage("");
    if (!supabase) {
      setError("Account services are not configured for this deployment yet.");
      return;
    }
    if (!email.trim()) {
      setError("Enter your email address first, then request a reset link.");
      return;
    }
    setBusy(true);
    try {
      const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + "/auth",
      });
      if (resetError) throw resetError;
      setMessage("If an account exists for this address, a password reset email is on its way.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send the reset email.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#F5F4EF] text-[#163238]">
      <div className="grid min-h-screen lg:grid-cols-[minmax(420px,0.9fr)_1.1fr]">
        <aside className="relative hidden min-h-screen overflow-hidden bg-[#143B3B] px-12 py-10 text-white lg:flex lg:flex-col">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_72%,rgba(239,128,91,0.16),transparent_30%),radial-gradient(circle_at_85%_24%,rgba(98,198,181,0.2),transparent_32%)]" />
          <Link href="/" className="relative flex items-center gap-3 text-xl font-bold tracking-tight">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#62C6B5] text-[#143B3B]">N</span>
            nomadsai
          </Link>
          <div className="relative my-auto max-w-xl pb-12">
            <span className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/5 px-4 py-2 text-xs font-semibold tracking-[0.18em] text-[#B9E2D6]">
              <Sparkles className="h-4 w-4" /> THOUGHTFUL TRAVEL STARTS HERE
            </span>
            <h1 className="max-w-lg text-5xl font-semibold leading-[1.08] tracking-tight xl:text-6xl">
              {recovery ? "Set a new password." : mode === "sign-up" ? "Make room for the journey." : "Pick up where you left off."}
            </h1>
            <p className="mt-7 max-w-md text-lg leading-8 text-[#C3D4CE]">
              {mode === "sign-up"
                ? "Discover places, plan your time and keep the memories that matter, all in one considered space."
                : "Your saved plans, destination research and private travel memories are ready when you are."}
            </p>
            <div className="relative mt-16 h-64 max-w-lg">
              <svg viewBox="0 0 560 300" className="h-full w-full" role="img" aria-label="Abstract route map illustration">
                <g fill="none" stroke="#78BFB0" strokeWidth="1.2" opacity=".3">
                  <path d="M-10 65 C60 20 100 48 144 82 S220 115 260 75 S340 25 380 66 S480 112 570 48" />
                  <path d="M-20 132 C55 92 92 132 142 154 S224 187 270 144 S355 100 405 141 S492 185 580 118" />
                  <path d="M-15 208 C40 174 98 196 148 228 S238 263 284 216 S362 175 414 211 S500 260 575 195" />
                </g>
                <path d="M74 220 C130 184 160 230 213 180 S290 65 355 102 S424 174 487 65" fill="none" stroke="#F39A73" strokeWidth="3" strokeLinecap="round" strokeDasharray="5 9" />
                <circle cx="74" cy="220" r="7" fill="#F39A73" />
                <circle cx="487" cy="65" r="9" fill="#F39A73" />
                <circle cx="487" cy="65" r="18" fill="none" stroke="#F39A73" opacity=".55" />
              </svg>
              <div className="absolute right-3 top-2 rounded-2xl border border-white/10 bg-[#1D4945]/90 p-4 shadow-xl backdrop-blur">
                <p className="text-[10px] font-bold tracking-widest text-[#B9E2D6]">YOUR NEXT CHAPTER</p>
                <p className="mt-1 font-semibold">Somewhere new.</p>
                <p className="mt-1 text-xs text-[#C3D4CE]">A plan that feels like yours</p>
              </div>
            </div>
          </div>
          <p className="relative text-xs text-[#A9C0B8]">Travel intelligence for the curious.</p>
        </aside>

        <section className="flex min-h-screen flex-col px-5 py-7 sm:px-10 lg:px-16 xl:px-24">
          <div className="flex items-center justify-between">
            <Link href="/" className="inline-flex items-center gap-2 text-sm font-semibold text-[#667A79] transition hover:text-[#14796E]">
              <ArrowLeft className="h-4 w-4" /> Back to NomadsAI
            </Link>
            <Link href="/" className="flex items-center gap-2 text-sm font-bold text-[#163238] lg:hidden">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#14796E] text-white">N</span> nomadsai
            </Link>
          </div>

          <div className="mx-auto flex w-full max-w-[460px] flex-1 flex-col justify-center py-12">
            <div className="mb-8">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#E2EEE8] text-[#14796E]">
                {mode === "sign-up" ? <Compass className="h-6 w-6" /> : <Globe2 className="h-6 w-6" />}
              </div>
              <p className="text-sm font-semibold text-[#14796E]">{recovery ? "Secure your account" : mode === "sign-up" ? "Your next journey starts here" : "Welcome back"}</p>
              <h2 className="mt-2 text-4xl font-semibold tracking-tight text-[#163238]">
                {recovery ? "Choose a new password" : mode === "sign-up" ? "Create your account" : "Sign in to NomadsAI"}
              </h2>
              <p className="mt-3 text-base leading-7 text-[#667A79]">
                {recovery ? "Your reset link is valid. Choose a new password to finish." : mode === "sign-up"
                  ? "Save your travel plans and keep your memories together."
                  : "Access your saved plans and private travel memories."}
              </p>
            </div>

            <div className="mb-7 grid grid-cols-2 rounded-2xl bg-[#E8F0EB] p-1.5" role="tablist" aria-label="Account access">
              <button type="button" role="tab" aria-selected={mode === "sign-in"} onClick={() => changeMode("sign-in")}
                className={"rounded-xl px-4 py-3 text-sm font-semibold transition " + (mode === "sign-in" ? "bg-white text-[#163238] shadow-sm" : "text-[#667A79] hover:text-[#163238]")}>
                Sign in
              </button>
              <button type="button" role="tab" aria-selected={mode === "sign-up"} onClick={() => changeMode("sign-up")}
                className={"rounded-xl px-4 py-3 text-sm font-semibold transition " + (mode === "sign-up" ? "bg-white text-[#163238] shadow-sm" : "text-[#667A79] hover:text-[#163238]")}>
                Create account
              </button>
            </div>

            <form onSubmit={submit} className="space-y-5">
              <label className="block text-sm font-semibold text-[#425A59]">
                Email address
                <input type="email" required autoComplete="email" value={email} onChange={event => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  className="mt-2.5 h-14 w-full rounded-xl border border-[#DDE5DF] bg-white px-4 text-base font-normal text-[#163238] outline-none transition placeholder:text-[#9AA9A4] focus:border-[#14796E] focus:ring-4 focus:ring-[#14796E]/10" />
              </label>
              <label className="block text-sm font-semibold text-[#425A59]">
                Password
                <span className="relative mt-2.5 block">
                  <input type={showPassword ? "text" : "password"} required minLength={8}
                    autoComplete={mode === "sign-in" ? "current-password" : "new-password"}
                    value={password} onChange={event => setPassword(event.target.value)}
                    placeholder={mode === "sign-up" ? "At least 8 characters" : "Your password"}
                    className="h-14 w-full rounded-xl border border-[#DDE5DF] bg-white px-4 pr-12 text-base font-normal text-[#163238] outline-none transition placeholder:text-[#9AA9A4] focus:border-[#14796E] focus:ring-4 focus:ring-[#14796E]/10" />
                  <button type="button" onClick={() => setShowPassword(value => !value)} aria-label={showPassword ? "Hide password" : "Show password"}
                    className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-[#84958F] hover:text-[#14796E]">
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </span>
                {(mode === "sign-up" || recovery) && <span className="mt-2 block text-xs font-normal text-[#84958F]">Use at least 8 characters.</span>}
              </label>

              {mode === "sign-in" && !recovery && (
                <div className="flex justify-end">
                  <button type="button" onClick={sendPasswordReset} disabled={busy}
                    className="text-sm font-semibold text-[#14796E] transition hover:text-[#105F57] disabled:opacity-50">
                    Forgot password?
                  </button>
                </div>
              )}

              {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
              {message && <p role="status" className="rounded-xl border border-[#BBDCCF] bg-[#EAF5EF] p-3 text-sm leading-6 text-[#21634F]">{message}</p>}

              <button type="submit" disabled={busy || !supabase}
                className="group flex h-14 w-full items-center justify-center gap-2 rounded-full bg-[#14796E] px-5 font-semibold text-white shadow-sm transition hover:bg-[#105F57] focus:outline-none focus:ring-4 focus:ring-[#14796E]/20 disabled:cursor-not-allowed disabled:opacity-50">
                {busy ? "Please wait…" : recovery ? "Update password" : mode === "sign-in" ? "Sign in" : "Create account"}
                {!busy && <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />}
              </button>
              {!supabase && <p className="text-xs text-amber-700">Account services are not configured for this deployment yet.</p>}
            </form>

            <p className="mt-7 text-center text-sm text-[#667A79]">
              {!recovery && <>{mode === "sign-in" ? "New to NomadsAI?" : "Already have an account?"}{" "}
              <button type="button" onClick={() => changeMode(mode === "sign-in" ? "sign-up" : "sign-in")}
                className="font-semibold text-[#14796E] hover:text-[#105F57]">
                {mode === "sign-in" ? "Create an account" : "Sign in"}
              </button></>}
            </p>
            <p className="mt-10 flex items-center justify-center gap-2 text-center text-xs text-[#84958F]">
              <MapPin className="h-3.5 w-3.5" /> Your travel memories remain private to your account.
            </p>
          </div>

          <footer className="pb-3 text-center text-xs text-[#9AA9A4]">
            NomadsAI · Travel intelligence for the curious
          </footer>
        </section>
      </div>
    </main>
  );
}
