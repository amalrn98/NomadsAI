"use client";

import { useState } from "react";
import Link from "next/link";
import { getSupabaseClient } from "@/lib/supabase";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function DigestPage() {
	const [region, setRegion] = useState("");
	const [status, setStatus] = useState<string | null>(null);
	const [needsSignIn, setNeedsSignIn] = useState(false);
	const [busy, setBusy] = useState(false);

	async function sendDigest() {
		setStatus(null);
		setNeedsSignIn(false);
		const supabase = getSupabaseClient();
		const { data } = supabase ? await supabase.auth.getSession() : { data: { session: null } };
		const token = data.session?.access_token;
		if (!token) {
			setNeedsSignIn(true);
			setStatus("Sign in to receive the digest at your account email.");
			return;
		}
		setBusy(true);
		try {
			const res = await fetch(`${API_BASE}/api/digest/send`, {
				method: "POST",
				headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
				body: JSON.stringify({ region: region || null }),
			});
			if (res.ok) setStatus("Sent! Check the inbox of your account email.");
			else if (res.status === 401) {
				setNeedsSignIn(true);
				setStatus("Your session expired. Please sign in again.");
			} else if (res.status === 429) setStatus("Too many requests. Please try again later.");
			else setStatus("The digest could not be sent. Please try again later.");
		} catch {
			setStatus("Could not reach the server. Please try again later.");
		} finally {
			setBusy(false);
		}
	}

	return (
		<div className="space-y-6">
			<h1 className="text-2xl font-semibold">Weekly Email Digest</h1>
			<p className="text-sm text-white/70">
				Get source-linked travel news sent to the email address on your account.
			</p>
			<div className="card grid md:grid-cols-2 gap-3">
				<select
					value={region}
					onChange={(e) => setRegion(e.target.value)}
					aria-label="Region"
					className="rounded bg-white/10 px-3 py-2 outline-none"
				>
					<option value="">All regions</option>
					<option>Europe</option>
					<option>Asia</option>
					<option>North America</option>
				</select>
				<div>
					<button
						onClick={sendDigest}
						disabled={busy}
						className="px-4 py-2 rounded bg-brand text-black font-medium hover:bg-brand-light disabled:opacity-60"
					>
						{busy ? "Sending…" : "Send me the latest news"}
					</button>
				</div>
			</div>
			{status && (
				<div className="text-sm text-white/70" role="status">
					{status}{" "}
					{needsSignIn && (
						<Link href="/auth" className="underline">
							Go to sign in
						</Link>
					)}
				</div>
			)}
		</div>
	);
}
