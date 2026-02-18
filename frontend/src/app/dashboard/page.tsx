"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { api, StatusResponse } from "@/lib/api";

function StatusBadge({ value }: { value: boolean | string }) {
  const ok = value === true || value === "online" || value === "ready";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${ok ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-green-400" : "bg-red-400"}`} />
      {typeof value === "boolean" ? (ok ? "Connected" : "Not connected") : value}
    </span>
  );
}

export default function DashboardOverview() {
  const { data: session } = useSession();
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = (session as any)?.accessToken;
    if (!token) return;
    api.status(token)
      .then(setStatus)
      .catch((e) => setError(e.message));
  }, [session]);

  return (
    <div>
      <h2 className="text-2xl font-bold text-white mb-1">Overview</h2>
      <p className="text-slate-400 text-sm mb-8">Real-time status of your Clubmate AI instance.</p>

      {error && (
        <div className="mb-6 rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-red-400 text-sm">
          Could not reach the API: <strong>{error}</strong>
          <br />
          <span className="text-xs text-red-500/70">Make sure your server is running and NEXT_PUBLIC_API_URL is set correctly.</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card title="Bot" value={status?.bot ?? "—"} label={<StatusBadge value={status?.bot === "online"} />} />
        <Card title="Google Account" value={status?.google_connected ? "Connected" : "Not connected"} label={<StatusBadge value={status?.google_connected ?? false} />} />
        <Card title="Knowledge Base" value={status ? `${status.rag.document_chunks} chunks` : "—"} label={<StatusBadge value={status?.rag.status ?? "—"} />} />
        <Card title="AI Model" value={status?.model ?? "—"} label={<span className="text-xs text-slate-500">Gemini</span>} />
        <Card title="Exec Role" value={status?.exec_role ?? "—"} label={<span className="text-xs text-slate-500">Set in Permissions</span>} />
      </div>
    </div>
  );
}

function Card({ title, value, label }: { title: string; value: string; label: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-[#16213e] p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-slate-400">{title}</span>
        {label}
      </div>
      <p className="text-xl font-semibold text-white">{value}</p>
    </div>
  );
}
