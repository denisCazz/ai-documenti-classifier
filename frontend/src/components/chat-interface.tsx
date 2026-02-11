"use client";

import { useState, useRef, useEffect } from "react";
import { sendChatMessage, checkChatHealth } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Array<{
    document_id: string;
    content_preview: string;
    similarity: number;
  }>;
  model_used?: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatReady, setChatReady] = useState<boolean | null>(null);
  const [chatInfo, setChatInfo] = useState<{
    model: string;
    provider: string;
  } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Verifica che la chat sia configurata all'avvio
  useEffect(() => {
    async function checkHealth() {
      try {
        const health = await checkChatHealth();
        setChatReady(true);
        setChatInfo({ model: health.model, provider: health.provider });
      } catch {
        setChatReady(false);
      }
    }
    checkHealth();
  }, []);

  // Auto-scroll ai nuovi messaggi
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setLoading(true);

    // Aggiungi il messaggio dell'utente
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      /**
       * NOTA IMPORTANTE:
       * sendChatMessage() invia il JWT token nell'header Authorization.
       * Il backend usa questo token per:
       * 1. Identificare l'utente (get_current_user)
       * 2. Risolvere il tenant/organizzazione (get_current_tenant_config)
       * 3. Caricare la API key OpenAI dal DB
       * 4. Eseguire la pipeline RAG con quella API key
       *
       * Il frontend NON invia e NON conosce la API key OpenAI.
       */
      const response = await sendChatMessage(userMessage);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          model_used: response.model_used,
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Errore: ${err.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  // Chat non configurata
  if (chatReady === false) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-4">
          <div className="text-4xl">⚙️</div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Chat non configurata
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md">
            L&apos;amministratore deve configurare la API key nelle{" "}
            <a
              href="/dashboard/settings"
              className="text-blue-600 hover:underline"
            >
              Settings
            </a>{" "}
            prima di poter usare la chat.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Chat Info Bar */}
      {chatInfo && (
        <div className="mb-4 flex items-center gap-2 text-xs text-gray-400 dark:text-gray-500">
          <span className="inline-block w-2 h-2 rounded-full bg-green-500" />
          <span>
            {chatInfo.provider} / {chatInfo.model}
          </span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-600">
            <p>Fai una domanda sui tuoi documenti...</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200"
              }`}
            >
              <p className="whitespace-pre-wrap text-sm">{msg.content}</p>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                    Fonti ({msg.sources.length}):
                  </p>
                  {msg.sources.map((source, j) => (
                    <div
                      key={j}
                      className="text-xs text-gray-400 dark:text-gray-500 mb-1 truncate"
                    >
                      [{j + 1}] {source.content_preview} (
                      {(source.similarity * 100).toFixed(0)}%)
                    </div>
                  ))}
                </div>
              )}

              {/* Model info */}
              {msg.model_used && (
                <div className="mt-1 text-xs text-gray-400 dark:text-gray-600">
                  via {msg.model_used}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl px-4 py-3">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="flex gap-3 pt-4 border-t border-gray-200 dark:border-gray-800"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Chiedi qualcosa sui tuoi documenti..."
          disabled={loading || chatReady === null}
          className="flex-1 rounded-xl border border-gray-300 px-4 py-3 dark:border-gray-700 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
        >
          Invia
        </button>
      </form>
    </div>
  );
}
