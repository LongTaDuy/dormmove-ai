"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "@/types";
import { DEMO_PROMPT } from "@/lib/constants";

const HELPER_TEXT =
  "Tell DormMove your dorm, room type, move-in date, budget, what you own, and what your roommate is bringing.";

export function ChatPanel({
  messages,
  onSend,
  loading,
  disabled,
}: {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  loading: boolean;
  disabled?: boolean;
}) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading || disabled) return;
    onSend(text);
    setInput("");
  }

  return (
    <div className="card flex min-h-[480px] flex-col overflow-hidden">
      <div className="border-b border-border bg-cream/40 px-5 py-4">
        <h2 className="text-lg font-semibold text-espresso">Move-in chat</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">{HELPER_TEXT}</p>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto bg-ivory p-5">
        {messages.length === 0 && (
          <p className="rounded-xl border border-dashed border-border bg-cream/30 px-4 py-8 text-center text-sm text-muted">
            Send a message or use the demo prompt below to generate your plan.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-brand text-white shadow-soft"
                  : "border border-border bg-cream text-espresso"
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-border bg-cream px-4 py-3 text-sm text-muted">
              Planning your move-in…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="space-y-3 border-t border-border bg-cream/30 p-5">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Example: double dorm at Denison, move-in Aug 24, $650 budget…"
          rows={3}
          disabled={loading || disabled}
          className="w-full resize-none rounded-xl border border-border bg-ivory px-4 py-3 text-base text-espresso placeholder:text-muted/70 focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20 disabled:opacity-50"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="submit"
            disabled={loading || disabled || !input.trim()}
            className="btn-primary min-w-[100px]"
          >
            Send
          </button>
          <button
            type="button"
            onClick={() => setInput(DEMO_PROMPT)}
            disabled={loading || disabled}
            className="btn-accent"
          >
            Use demo prompt
          </button>
        </div>
      </form>
    </div>
  );
}
