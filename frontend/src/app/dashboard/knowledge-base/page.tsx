"use client";

import { useSession } from "next-auth/react";
import { useEffect, useRef, useState } from "react";
import { api, RagStatus } from "@/lib/api";

export default function KnowledgeBasePage() {
  const { data: session } = useSession();
  const [ragStatus, setRagStatus] = useState<RagStatus | null>(null);
  const [docUrl, setDocUrl] = useState("");
  const [loading, setLoading] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const token = (session as any)?.accessToken;

  const refresh = () => api.rag.status(token).then(setRagStatus).catch(() => {});

  useEffect(() => {
    if (!token) return;
    refresh();
  }, [token]);

  async function ingestDoc() {
    if (!docUrl.trim()) return;
    setLoading("doc");
    setMsg(null);
    try {
      const res = await api.rag.ingestGoogleDoc(token, docUrl);
      setMsg({ type: "success", text: res.message });
      setDocUrl("");
      await refresh();
    } catch (e: any) {
      setMsg({ type: "error", text: e.message });
    } finally {
      setLoading(null);
    }
  }

  async function ingestFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading("file");
    setMsg(null);
    try {
      const res = await api.rag.ingestFile(token, file);
      setMsg({ type: "success", text: res.message });
      await refresh();
    } catch (e: any) {
      setMsg({ type: "error", text: e.message });
    } finally {
      setLoading(null);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function resetKb() {
    if (!confirm("Clear the entire knowledge base? This cannot be undone.")) return;
    setLoading("reset");
    setMsg(null);
    try {
      const res = await api.rag.reset(token);
      setMsg({ type: "success", text: res.message });
      await refresh();
    } catch (e: any) {
      setMsg({ type: "error", text: e.message });
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="max-w-xl">
      <h2 className="text-2xl font-bold text-white mb-1">Knowledge Base</h2>
      <p className="text-slate-400 text-sm mb-8">
        Add documents so members can ask questions and get answers via <code className="text-[#5865F2]">/ask</code>.
      </p>

      {/* Status */}
      <div className="rounded-xl border border-white/10 bg-[#16213e] p-4 mb-6 flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-white">
            {ragStatus?.chunk_count ?? "—"} document chunks
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            Status: {ragStatus?.status ?? "loading..."}
          </p>
        </div>
        {ragStatus?.has_documents && (
          <button
            onClick={resetKb}
            disabled={!!loading}
            className="rounded-lg bg-red-500/20 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/30 transition disabled:opacity-50"
          >
            {loading === "reset" ? "Clearing..." : "Clear all"}
          </button>
        )}
      </div>

      {msg && (
        <div className={`mb-5 rounded-xl px-4 py-3 text-sm border ${msg.type === "success" ? "bg-green-500/10 border-green-500/20 text-green-400" : "bg-red-500/10 border-red-500/20 text-red-400"}`}>
          {msg.text}
        </div>
      )}

      <div className="space-y-4">
        {/* Google Doc */}
        <div className="rounded-xl border border-white/10 bg-[#16213e] p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Sync a Google Doc</h3>
          <p className="text-xs text-slate-500 mb-3">Paste a Google Doc URL (e.g. your club FAQ doc). The content will be indexed automatically.</p>
          <div className="flex gap-2">
            <input
              type="url"
              value={docUrl}
              onChange={(e) => setDocUrl(e.target.value)}
              placeholder="https://docs.google.com/document/d/..."
              className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-[#5865F2]"
            />
            <button
              onClick={ingestDoc}
              disabled={!docUrl.trim() || !!loading}
              className="rounded-lg bg-[#5865F2] px-4 py-2 text-sm font-medium text-white hover:bg-[#4752c4] transition disabled:opacity-50"
            >
              {loading === "doc" ? "Syncing..." : "Sync"}
            </button>
          </div>
        </div>

        {/* File upload */}
        <div className="rounded-xl border border-white/10 bg-[#16213e] p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Upload a file</h3>
          <p className="text-xs text-slate-500 mb-3">Supports PDF, TXT, and Markdown files.</p>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.txt,.md,.markdown"
            className="hidden"
            onChange={ingestFile}
          />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={!!loading}
            className="w-full rounded-lg border-2 border-dashed border-white/10 px-4 py-6 text-sm text-slate-400 hover:border-[#5865F2]/50 hover:text-slate-300 transition disabled:opacity-50 text-center"
          >
            {loading === "file" ? "Uploading..." : "Click to upload a file"}
          </button>
        </div>
      </div>
    </div>
  );
}
