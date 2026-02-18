"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { api, ConfigResponse } from "@/lib/api";

export default function PermissionsPage() {
  const { data: session } = useSession();
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [execRole, setExecRole] = useState("");
  const [summaryChannelId, setSummaryChannelId] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const token = (session as any)?.accessToken;

  useEffect(() => {
    if (!token) return;
    api.config.get(token).then((c) => {
      setConfig(c);
      setExecRole(c.exec_role_name);
      setSummaryChannelId(c.meeting_summary_channel_id);
    });
  }, [token]);

  async function save() {
    setLoading(true);
    setMsg(null);
    try {
      await api.config.update(token, {
        exec_role_name: execRole,
        meeting_summary_channel_id: summaryChannelId,
      });
      setMsg({ type: "success", text: "Saved. Restart the bot for changes to take effect." });
    } catch (e: any) {
      setMsg({ type: "error", text: e.message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl">
      <h2 className="text-2xl font-bold text-white mb-1">Permissions</h2>
      <p className="text-slate-400 text-sm mb-8">
        Control who can use exec-only commands and where meeting summaries are posted.
      </p>

      {msg && (
        <div className={`mb-5 rounded-xl px-4 py-3 text-sm border ${msg.type === "success" ? "bg-green-500/10 border-green-500/20 text-green-400" : "bg-red-500/10 border-red-500/20 text-red-400"}`}>
          {msg.text}
        </div>
      )}

      <div className="space-y-5">
        <div className="rounded-xl border border-white/10 bg-[#16213e] p-5">
          <label className="block text-sm font-medium text-white mb-1">
            Exec Role Name
          </label>
          <p className="text-xs text-slate-500 mb-3">
            Discord role that grants access to exec-only commands like <code className="text-[#5865F2]">/schedule</code>, <code className="text-[#5865F2]">/create-form</code>, etc. Must match exactly (case-insensitive).
          </p>
          <input
            type="text"
            value={execRole}
            onChange={(e) => setExecRole(e.target.value)}
            placeholder="Executive"
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-[#5865F2]"
          />
        </div>

        <div className="rounded-xl border border-white/10 bg-[#16213e] p-5">
          <label className="block text-sm font-medium text-white mb-1">
            Meeting Summary Channel ID
          </label>
          <p className="text-xs text-slate-500 mb-3">
            Discord channel ID where meeting summaries are posted after <code className="text-[#5865F2]">/meeting end</code>. Right-click a channel → Copy Channel ID (Developer Mode must be on).
          </p>
          <input
            type="text"
            value={summaryChannelId}
            onChange={(e) => setSummaryChannelId(e.target.value)}
            placeholder="1234567890123456789"
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-[#5865F2]"
          />
        </div>

        <button
          onClick={save}
          disabled={loading}
          className="w-full rounded-xl bg-[#5865F2] px-4 py-3 text-sm font-semibold text-white hover:bg-[#4752c4] transition disabled:opacity-50"
        >
          {loading ? "Saving..." : "Save Changes"}
        </button>
      </div>
    </div>
  );
}
