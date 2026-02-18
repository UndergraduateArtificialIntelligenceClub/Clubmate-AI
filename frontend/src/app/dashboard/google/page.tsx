"use client";

import { useSession } from "next-auth/react";
import { useEffect, useRef, useState } from "react";
import { api, GoogleStatus } from "@/lib/api";

export default function GoogleAccountPage() {
  const { data: session } = useSession();
  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [credJson, setCredJson] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const token = (session as any)?.accessToken;

  useEffect(() => {
    if (!token) return;
    api.google.status(token).then(setStatus).catch(() => {});
  }, [token]);

  async function handleUploadCredentials() {
    if (!credJson.trim()) return;
    setLoading(true);
    setMsg(null);
    try {
      await api.google.uploadCredentials(token, credJson);
      const { auth_url } = await api.google.startAuth(token);
      // Open OAuth in current tab — callback returns to the API
      window.location.href = auth_url;
    } catch (e: any) {
      setMsg({ type: "error", text: e.message });
    } finally {
      setLoading(false);
    }
  }

  async function handleDisconnect() {
    if (!confirm("Disconnect your Google account? Calendar, Docs, Sheets, and Forms will stop working.")) return;
    setLoading(true);
    try {
      await api.google.disconnect(token);
      setStatus({ connected: false, account_email: null });
      setMsg({ type: "success", text: "Google account disconnected." });
    } catch (e: any) {
      setMsg({ type: "error", text: e.message });
    } finally {
      setLoading(false);
    }
  }

  function handleFileRead(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setCredJson(ev.target?.result as string);
    reader.readAsText(file);
  }

  return (
    <div className="max-w-xl">
      <h2 className="text-2xl font-bold text-white mb-1">Google Account</h2>
      <p className="text-slate-400 text-sm mb-8">
        Connect your club&apos;s Google account to enable Calendar, Docs, Sheets, and Forms features.
      </p>

      {msg && (
        <div className={`mb-5 rounded-xl px-4 py-3 text-sm border ${msg.type === "success" ? "bg-green-500/10 border-green-500/20 text-green-400" : "bg-red-500/10 border-red-500/20 text-red-400"}`}>
          {msg.text}
        </div>
      )}

      {status?.connected ? (
        <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-5 mb-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="h-2 w-2 rounded-full bg-green-400" />
            <span className="text-sm font-medium text-green-400">Connected</span>
          </div>
          {status.account_email && (
            <p className="text-slate-300 text-sm">{status.account_email}</p>
          )}
          <button
            onClick={handleDisconnect}
            disabled={loading}
            className="mt-4 rounded-lg bg-red-500/20 px-3 py-1.5 text-sm text-red-400 hover:bg-red-500/30 transition disabled:opacity-50"
          >
            Disconnect Google Account
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="rounded-xl border border-white/10 bg-[#16213e] p-5">
            <h3 className="text-sm font-semibold text-white mb-3">Step 1 — Get your credentials</h3>
            <ol className="list-decimal list-inside space-y-1.5 text-sm text-slate-400">
              <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noreferrer" className="text-[#5865F2] hover:underline">Google Cloud Console</a></li>
              <li>Create a project → Enable Calendar, Docs, Sheets, Forms APIs</li>
              <li>Go to APIs &amp; Services → Credentials → Create OAuth 2.0 Client ID</li>
              <li>Application type: Web application</li>
              <li>Download the JSON file</li>
            </ol>
          </div>

          <div className="rounded-xl border border-white/10 bg-[#16213e] p-5">
            <h3 className="text-sm font-semibold text-white mb-3">Step 2 — Upload credentials &amp; connect</h3>
            <div className="space-y-3">
              <input
                ref={fileRef}
                type="file"
                accept=".json"
                className="hidden"
                onChange={handleFileRead}
              />
              <button
                onClick={() => fileRef.current?.click()}
                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-slate-300 hover:bg-white/10 transition text-left"
              >
                {credJson ? "credentials.json loaded ✓" : "Select credentials.json file"}
              </button>
              {credJson && (
                <button
                  onClick={handleUploadCredentials}
                  disabled={loading}
                  className="w-full rounded-lg bg-[#5865F2] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#4752c4] transition disabled:opacity-50"
                >
                  {loading ? "Connecting..." : "Connect Google Account"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
