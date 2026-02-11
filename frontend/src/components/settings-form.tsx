"use client";

import { useState, useEffect } from "react";
import { getSettings, updateSettings, getCurrentUser } from "@/lib/api";

interface SettingsData {
  org_id: string;
  provider: string;
  model_name: string;
  system_prompt: string;
  api_key_configured: boolean;
  api_key_preview: string | null;
}

export default function SettingsForm() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Form state
  const [apiKey, setApiKey] = useState("");
  const [modelName, setModelName] = useState("gpt-4o-mini");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [provider, setProvider] = useState("openai");

  useEffect(() => {
    async function loadData() {
      try {
        const [settingsData, userData] = await Promise.all([
          getSettings(),
          getCurrentUser(),
        ]);

        setSettings(settingsData);
        setIsAdmin(userData.role === "admin");

        // Prepopola il form con i dati esistenti
        setModelName(settingsData.model_name || "gpt-4o-mini");
        setSystemPrompt(settingsData.system_prompt || "");
        setProvider(settingsData.provider || "openai");
      } catch (err: any) {
        setMessage({ type: "error", text: err.message });
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!isAdmin) {
      setMessage({
        type: "error",
        text: "Solo gli amministratori possono modificare le settings.",
      });
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      const updateData: Record<string, string> = {};

      // Invia solo i campi che l'utente ha compilato
      if (apiKey) updateData.api_key = apiKey;
      if (modelName) updateData.model_name = modelName;
      if (systemPrompt) updateData.system_prompt = systemPrompt;
      if (provider) updateData.provider = provider;

      const result = await updateSettings(updateData);
      setSettings(result);
      setApiKey(""); // Pulisci il campo API key dopo il salvataggio

      setMessage({
        type: "success",
        text: "Configurazione aggiornata con successo!",
      });
    } catch (err: any) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500 dark:text-gray-400">
          Caricamento configurazione...
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl">
      {/* Status Message */}
      {message && (
        <div
          className={`p-4 rounded-lg text-sm ${
            message.type === "success"
              ? "bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400"
              : "bg-red-50 text-red-700 dark:bg-red-900/20 dark:text-red-400"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Admin Notice */}
      {!isAdmin && (
        <div className="p-4 rounded-lg bg-yellow-50 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400 text-sm">
          Solo gli amministratori possono modificare la configurazione.
          Visualizzazione in sola lettura.
        </div>
      )}

      {/* API Key Status */}
      <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Stato API Key
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {settings?.api_key_configured
                ? `Configurata: ${settings.api_key_preview}`
                : "Non configurata"}
            </p>
          </div>
          <span
            className={`px-2.5 py-1 rounded-full text-xs font-medium ${
              settings?.api_key_configured
                ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
            }`}
          >
            {settings?.api_key_configured ? "Attiva" : "Mancante"}
          </span>
        </div>
      </div>

      {/* Provider */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Provider AI
        </label>
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          disabled={!isAdmin}
          className="w-full rounded-lg border border-gray-300 px-4 py-3 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
        >
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic</option>
          <option value="mistral">Mistral AI</option>
        </select>
      </div>

      {/* API Key */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          API Key
        </label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          disabled={!isAdmin}
          placeholder={
            settings?.api_key_configured
              ? "Lascia vuoto per mantenere la key attuale"
              : "sk-..."
          }
          className="w-full rounded-lg border border-gray-300 px-4 py-3 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
        />
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          La chiave viene salvata in modo sicuro nel database e non viene mai
          esposta al frontend.
        </p>
      </div>

      {/* Model Name */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Modello
        </label>
        <select
          value={modelName}
          onChange={(e) => setModelName(e.target.value)}
          disabled={!isAdmin}
          className="w-full rounded-lg border border-gray-300 px-4 py-3 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
        >
          <option value="gpt-4o-mini">GPT-4o Mini</option>
          <option value="gpt-4o">GPT-4o</option>
          <option value="gpt-4-turbo">GPT-4 Turbo</option>
          <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
        </select>
      </div>

      {/* System Prompt */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          System Prompt
        </label>
        <textarea
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          disabled={!isAdmin}
          rows={5}
          placeholder='Es: "Rispondi come un ingegnere elettrico esperto..."'
          className="w-full rounded-lg border border-gray-300 px-4 py-3 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-blue-500 disabled:opacity-60 resize-y"
        />
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          Personalizza il comportamento dell&apos;AI per la tua organizzazione.
        </p>
      </div>

      {/* Submit */}
      {isAdmin && (
        <button
          type="submit"
          disabled={saving}
          className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
        >
          {saving ? "Salvataggio..." : "Salva Configurazione"}
        </button>
      )}
    </form>
  );
}
