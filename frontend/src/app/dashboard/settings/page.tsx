"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Keys settings panel for sensitive tokens — writes directly to .env on the server
interface ApiKeysForm {
  discord_token: string;
  discord_client_id: string;
  discord_client_secret: string;
  discord_guild_id: string;
  gemini_api_key: string;
}

async function updateApiKeys(token: string, keys: Partial<ApiKeysForm>) {
  const res = await fetch(`${API_URL}/config/keys`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(keys),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

export default function SettingsPage() {
  const { data: session } = useSession();
  const [model, setModel] = useState("");
  const [whisperMode, setWhisperMode] = useState("gemini");
  const [topK, setTopK] = useState("5");

  // API key fields — intentionally blank on load (never expose existing values to frontend)
  const [keys, setKeys] = useState<ApiKeysForm>({
    discord_token: "",
    discord_client_id: "",
    discord_client_secret: "",
    discord_guild_id: "",
    gemini_api_key: "",
  });

  const [loading, setLoading] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string; for?: string } | null>(null);

  const token = (session as { accessToken?: string } | null)?.accessToken;

  useEffect(() => {
    if (!token) return;
    api.config.get(token).then((c) => {
      setModel(c.default_llm_model);
      setWhisperMode(c.whisper_mode);
      setTopK(String(c.top_k_results));
    });
  }, [token]);

  async function saveGeneralSettings() {
    if (!token) {
      setMsg({ type: "error", text: "Not authenticated.", for: "general" });
      return;
    }
    setLoading("general");
    setMsg(null);
    try {
      await api.config.update(token, {
        default_llm_model: model,
        whisper_mode: whisperMode,
        top_k_results: parseInt(topK),
      });
      setMsg({ type: "success", text: "Settings saved. Restart the bot to apply.", for: "general" });
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Failed to save settings.";
      setMsg({ type: "error", text: message, for: "general" });
    } finally {
      setLoading(null);
    }
  }

  async function saveApiKeys() {
    if (!token) {
      setMsg({ type: "error", text: "Not authenticated.", for: "keys" });
      return;
    }
    const dirty = Object.fromEntries(
      Object.entries(keys).filter(([, v]) => v.trim() !== "")
    );
    if (Object.keys(dirty).length === 0) {
      setMsg({ type: "error", text: "Enter at least one key to update.", for: "keys" });
      return;
    }
    setLoading("keys");
    setMsg(null);
    try {
      await updateApiKeys(token, dirty);
      setKeys({ discord_token: "", discord_client_id: "", discord_client_secret: "", discord_guild_id: "", gemini_api_key: "" });
      setMsg({ type: "success", text: "API keys updated. Restart the bot for changes to take effect.", for: "keys" });
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Failed to update API keys.";
      setMsg({ type: "error", text: message, for: "keys" });
    } finally {
      setLoading(null);
    }
  }

  const MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
  ];

  return (
    <div className="max-w-xl space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white mb-1">Settings</h2>
        <p className="text-slate-400 text-sm">Configure API keys and bot behaviour.</p>
      </div>

      {/* API Keys */}
      <section className="rounded-xl border border-white/10 bg-[#16213e] p-5 space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-white">API Keys</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Leave a field blank to keep the existing value. Keys are stored only on your server — never sent to Vercel.
          </p>
        </div>

        {msg?.for === "keys" && (
          <Msg type={msg.type} text={msg.text} />
        )}

        <Field label="Discord Bot Token" value={keys.discord_token} onChange={(v) => setKeys({ ...keys, discord_token: v })} placeholder="MTQ…" secret />
        <Field label="Discord Client ID" value={keys.discord_client_id} onChange={(v) => setKeys({ ...keys, discord_client_id: v })} placeholder="1234567890" />
        <Field label="Discord Client Secret" value={keys.discord_client_secret} onChange={(v) => setKeys({ ...keys, discord_client_secret: v })} placeholder="abc123…" secret />
        <Field label="Discord Guild ID" value={keys.discord_guild_id} onChange={(v) => setKeys({ ...keys, discord_guild_id: v })} placeholder="9876543210" />
        <Field label="Gemini API Key" value={keys.gemini_api_key} onChange={(v) => setKeys({ ...keys, gemini_api_key: v })} placeholder="AIza…" secret />

        <button
          onClick={saveApiKeys}
          disabled={loading === "keys"}
          className="w-full rounded-xl bg-[#5865F2] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#4752c4] transition disabled:opacity-50"
        >
          {loading === "keys" ? "Saving..." : "Update API Keys"}
        </button>
      </section>

      {/* General settings */}
      <section className="rounded-xl border border-white/10 bg-[#16213e] p-5 space-y-4">
        <h3 className="text-sm font-semibold text-white">Bot Behaviour</h3>

        {msg?.for === "general" && (
          <Msg type={msg.type} text={msg.text} />
        )}

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5">Gemini Model</label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-[#5865F2]"
          >
            {MODELS.map((m) => <option key={m} value={m} className="bg-[#16213e]">{m}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5">Meeting Transcription</label>
          <select
            value={whisperMode}
            onChange={(e) => setWhisperMode(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-[#5865F2]"
          >
            <option value="gemini" className="bg-[#16213e]">Gemini Audio (recommended, uses Gemini API key)</option>
            <option value="local" className="bg-[#16213e]">Local Whisper (free, runs on your server)</option>
            <option value="api" className="bg-[#16213e]">OpenAI Whisper API (faster, requires OpenAI key)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1.5">
            RAG Top-K Results <span className="text-slate-500">(chunks retrieved per query)</span>
          </label>
          <input
            type="number"
            min={1}
            max={20}
            value={topK}
            onChange={(e) => setTopK(e.target.value)}
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-[#5865F2]"
          />
        </div>

        <button
          onClick={saveGeneralSettings}
          disabled={loading === "general"}
          className="w-full rounded-xl bg-[#5865F2] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#4752c4] transition disabled:opacity-50"
        >
          {loading === "general" ? "Saving..." : "Save Settings"}
        </button>
      </section>
    </div>
  );
}

function Field({ label, value, onChange, placeholder, secret = false }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  secret?: boolean;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-400 mb-1">{label}</label>
      <input
        type={secret ? "password" : "text"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-[#5865F2]"
      />
    </div>
  );
}

function Msg({ type, text }: { type: "success" | "error"; text: string }) {
  return (
    <div className={`rounded-lg px-3 py-2.5 text-xs border ${type === "success" ? "bg-green-500/10 border-green-500/20 text-green-400" : "bg-red-500/10 border-red-500/20 text-red-400"}`}>
      {text}
    </div>
  );
}
