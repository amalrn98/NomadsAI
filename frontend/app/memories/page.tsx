"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import type { Session } from "@supabase/supabase-js";
import { Calendar, Camera, MapPin, Plus, Trash2, LogOut, Pencil } from "lucide-react";
import { getSupabaseClient } from "@/lib/supabase";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
type Memory = {
  id: string; title: string; content: string; destination: string; created_at: string;
  image_url: string | null; mood: string | null; weather: string | null; companions: string[];
};
const SAMPLE_IMAGES = [
  "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
  "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=800&h=600&fit=crop",
  "https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?w=800&h=600&fit=crop",
];

export default function MemoriesPage() {
  const supabase = useMemo(() => getSupabaseClient(), []);
  const [session, setSession] = useState<Session | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [memories, setMemories] = useState<Memory[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [destination, setDestination] = useState("");
  const [mood, setMood] = useState("");
  const [weather, setWeather] = useState("");
  const [companions, setCompanions] = useState("");
  const [imageUrl, setImageUrl] = useState(SAMPLE_IMAGES[0]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!supabase) { setAuthReady(true); return; }
    let active = true;
    supabase.auth.getSession().then(({ data }) => {
      if (active) { setSession(data.session); setAuthReady(true); }
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setAuthReady(true);
    });
    return () => { active = false; subscription.unsubscribe(); };
  }, [supabase]);

  useEffect(() => {
    if (!session?.access_token) { setMemories([]); return; }
    const controller = new AbortController();
    async function load() {
      setError("");
      try {
        const response = await fetch(API_BASE + "/api/memory/", {
          headers: { Authorization: "Bearer " + session!.access_token },
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(response.status === 401 ? "Your session expired. Sign in again." : "Could not load travel memories.");
        setMemories(await response.json());
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "Could not load travel memories.");
      }
    }
    load();
    return () => controller.abort();
  }, [session?.access_token]);

  async function addMemory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch(API_BASE + "/api/memory/" + (editingId || ""), {
        method: editingId ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json", Authorization: "Bearer " + session.access_token },
        body: JSON.stringify({
          title, content, destination, image_url: imageUrl || null,
          mood: mood || null, weather: weather || null,
          companions: companions.split(",").map(value => value.trim()).filter(Boolean),
        }),
      });
      if (!response.ok) throw new Error(response.status === 401 ? "Your session expired. Sign in again." : "Could not save this memory.");
      const saved: Memory = await response.json();
      if (editingId) {
        setMemories(current => current.map(memory => memory.id === editingId ? saved : memory));
      } else {
        setMemories(current => [saved, ...current]);
      }
      setTitle(""); setContent(""); setDestination(""); setMood(""); setWeather("");
      setCompanions(""); setImageUrl(SAMPLE_IMAGES[0]); setEditingId(null); setShowForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save this memory.");
    } finally { setBusy(false); }
  }

  function startEdit(memory: Memory) {
    setEditingId(memory.id);
    setTitle(memory.title);
    setContent(memory.content);
    setDestination(memory.destination);
    setMood(memory.mood || "");
    setWeather(memory.weather || "");
    setCompanions(memory.companions.join(", "));
    setImageUrl(memory.image_url || SAMPLE_IMAGES[0]);
    setShowForm(true);
    setError("");
  }

  async function deleteMemory(id: string) {
    if (!session || !window.confirm("Delete this travel memory? This cannot be undone.")) return;
    setError("");
    try {
      const response = await fetch(API_BASE + "/api/memory/" + id, {
        method: "DELETE", headers: { Authorization: "Bearer " + session.access_token },
      });
      if (!response.ok) throw new Error(response.status === 404 ? "Memory not found." : "Could not delete this memory.");
      setMemories(current => current.filter(memory => memory.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete this memory.");
    }
  }

  async function signOut() {
    if (!supabase) return;
    await supabase.auth.signOut();
    setMemories([]);
  }

  if (!authReady) return <main className="min-h-screen bg-slate-950 p-10 text-center text-slate-300">Loading account…</main>;
  if (!supabase) return (
    <main className="min-h-screen bg-slate-950 px-4 py-20 text-center text-white">
      <Camera className="mx-auto h-12 w-12 text-cyan-300" /><h1 className="mt-4 text-3xl font-semibold">Travel Memories</h1>
      <p className="mx-auto mt-3 max-w-lg text-slate-400">Account services are not configured for this deployment yet.</p>
    </main>
  );
  if (!session) return (
    <main className="min-h-screen bg-slate-950 px-4 py-20 text-center text-white">
      <Camera className="mx-auto h-12 w-12 text-cyan-300" /><h1 className="mt-4 text-3xl font-semibold">Your Travel Memories</h1>
      <p className="mx-auto mt-3 max-w-lg text-slate-400">Sign in to create, view, and manage memories that are private to your account.</p>
      <Link href="/auth" className="mt-6 inline-flex rounded-lg bg-cyan-400 px-5 py-3 font-semibold text-slate-950">Sign in or create an account</Link>
    </main>
  );

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-10 text-white">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium uppercase tracking-widest text-cyan-300">Your account</p>
            <h1 className="mt-2 flex items-center gap-3 text-3xl font-semibold"><Camera className="h-8 w-8 text-cyan-300" />Travel Memories</h1>
            <p className="mt-2 text-slate-400">Private memories saved to your account.</p>
            <p className="mt-1 text-xs text-slate-500">{session.user.email}</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => { setEditingId(null); setTitle(""); setContent(""); setDestination(""); setMood(""); setWeather(""); setCompanions(""); setImageUrl(SAMPLE_IMAGES[0]); setShowForm(value => !value); }} className="inline-flex items-center gap-2 rounded-lg bg-cyan-400 px-4 py-2.5 font-semibold text-slate-950"><Plus className="h-4 w-4" />New memory</button>
            <button onClick={signOut} className="inline-flex items-center gap-2 rounded-lg border border-white/15 px-4 py-2.5 text-slate-300"><LogOut className="h-4 w-4" />Sign out</button>
          </div>
        </div>
        {error && <p role="alert" className="mt-6 rounded-lg border border-red-500/30 bg-red-950/40 p-3 text-sm text-red-200">{error}</p>}
        {showForm && (
          <form onSubmit={addMemory} className="mt-8 grid gap-4 rounded-2xl border border-white/10 bg-slate-900 p-6 md:grid-cols-2">
            <label className="text-sm text-slate-300">Title
              <input required maxLength={160} value={title} onChange={event => setTitle(event.target.value)} className="mt-2 w-full rounded-lg bg-slate-800 px-3 py-2.5 text-white" placeholder="Sunset at Santorini" />
            </label>
            <label className="text-sm text-slate-300">Destination
              <input required maxLength={160} value={destination} onChange={event => setDestination(event.target.value)} className="mt-2 w-full rounded-lg bg-slate-800 px-3 py-2.5 text-white" placeholder="Santorini, Greece" />
            </label>
            <label className="text-sm text-slate-300 md:col-span-2">Your story
              <textarea maxLength={10000} rows={4} value={content} onChange={event => setContent(event.target.value)} className="mt-2 w-full rounded-lg bg-slate-800 px-3 py-2.5 text-white" placeholder="What do you want to remember?" />
            </label>
            <label className="text-sm text-slate-300">Mood
              <select value={mood} onChange={event => setMood(event.target.value)} className="mt-2 w-full rounded-lg bg-slate-800 px-3 py-2.5 text-white">
                <option value="">Not specified</option><option value="adventure">Adventure</option><option value="relaxed">Relaxed</option><option value="cultural">Cultural</option><option value="romantic">Romantic</option><option value="foodie">Foodie</option><option value="nature">Nature</option>
              </select>
            </label>
            <label className="text-sm text-slate-300">Weather
              <select value={weather} onChange={event => setWeather(event.target.value)} className="mt-2 w-full rounded-lg bg-slate-800 px-3 py-2.5 text-white">
                <option value="">Not specified</option><option value="sunny">Sunny</option><option value="cloudy">Cloudy</option><option value="rainy">Rainy</option><option value="snowy">Snowy</option>
              </select>
            </label>
            <label className="text-sm text-slate-300">Travel companions
              <input value={companions} onChange={event => setCompanions(event.target.value)} className="mt-2 w-full rounded-lg bg-slate-800 px-3 py-2.5 text-white" placeholder="Names, separated by commas" />
            </label>
            <label className="text-sm text-slate-300">Photo
              <select value={imageUrl} onChange={event => setImageUrl(event.target.value)} className="mt-2 w-full rounded-lg bg-slate-800 px-3 py-2.5 text-white">
                {SAMPLE_IMAGES.map((url, index) => <option key={url} value={url}>Travel photo {index + 1}</option>)}
              </select>
            </label>
            <div className="flex justify-end gap-3 md:col-span-2">
              <button type="button" onClick={() => { setShowForm(false); setEditingId(null); }} className="rounded-lg border border-white/15 px-4 py-2 text-slate-300">Cancel</button>
              <button type="submit" disabled={busy} className="rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-950 disabled:opacity-50">{busy ? "Saving…" : editingId ? "Update memory" : "Save memory"}</button>
            </div>
          </form>
        )}
        {memories.length === 0 ? (
          <div className="mt-16 rounded-2xl border border-dashed border-white/15 py-16 text-center">
            <Camera className="mx-auto h-12 w-12 text-slate-600" /><h2 className="mt-4 text-xl font-semibold">No memories yet</h2>
            <p className="mt-2 text-slate-400">Create your first travel memory.</p>
          </div>
        ) : (
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {memories.map(memory => (
              <article key={memory.id} className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900">
                <img src={memory.image_url || SAMPLE_IMAGES[0]} alt="" className="h-48 w-full object-cover" />
                <div className="p-5">
                  <div className="flex items-start justify-between gap-3">
                    <h2 className="text-lg font-semibold">{memory.title}</h2>
                    <button onClick={() => startEdit(memory)} aria-label={"Edit " + memory.title} className="text-slate-400 hover:text-cyan-300"><Pencil className="h-4 w-4" /></button>
                  </div>
                  <p className="mt-2 flex items-center gap-2 text-sm text-slate-400"><MapPin className="h-4 w-4" />{memory.destination}</p>
                  <p className="mt-1 flex items-center gap-2 text-xs text-slate-500"><Calendar className="h-3.5 w-3.5" />{new Date(memory.created_at).toLocaleDateString()}</p>
                  {memory.content && <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-slate-300">{memory.content}</p>}
                  {(memory.mood || memory.weather) && <p className="mt-3 text-xs text-cyan-300">{[memory.mood, memory.weather].filter(Boolean).join(" · ")}</p>}
                  {memory.companions?.length > 0 && <p className="mt-2 text-xs text-slate-400">With {memory.companions.join(", ")}</p>}
                  <button onClick={() => deleteMemory(memory.id)} className="mt-5 inline-flex items-center gap-2 text-sm text-red-300 hover:text-red-200"><Trash2 className="h-4 w-4" />Delete</button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
