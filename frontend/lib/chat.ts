import type { ChatMessage, SessionMessage, TraceEntry } from "@/types";

/** Map persisted session messages to chat bubbles (user + assistant only). */
export function messagesFromSnapshot(
  messages: SessionMessage[],
): ChatMessage[] {
  return messages
    .filter((m) => m.role === "user" || m.role === "assistant")
    .map((m) => ({
      role: m.role as "user" | "assistant",
      content: m.content,
    }));
}

/** Pull trace from the most recent assistant message metadata. */
export function traceFromSnapshot(messages: SessionMessage[]): TraceEntry[] {
  for (let i = messages.length - 1; i >= 0; i--) {
    const meta = messages[i].meta;
    if (messages[i].role === "assistant" && Array.isArray(meta?.trace)) {
      return meta.trace as TraceEntry[];
    }
  }
  return [];
}

export function riskFlagsFromSnapshot(
  messages: SessionMessage[],
  planFlags: string[] = [],
): string[] {
  for (let i = messages.length - 1; i >= 0; i--) {
    const meta = messages[i].meta;
    if (messages[i].role === "assistant" && Array.isArray(meta?.risk_flags)) {
      return meta.risk_flags as string[];
    }
  }
  return planFlags;
}

export function missingFieldsFromSnapshot(
  messages: SessionMessage[],
): string[] {
  for (let i = messages.length - 1; i >= 0; i--) {
    const meta = messages[i].meta;
    if (messages[i].role === "assistant" && Array.isArray(meta?.missing_fields)) {
      return meta.missing_fields as string[];
    }
  }
  return [];
}
