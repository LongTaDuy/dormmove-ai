import { SESSION_STORAGE_KEY } from "./constants";

export function getStoredSessionId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(SESSION_STORAGE_KEY);
}

export function setStoredSessionId(sessionId: string): void {
  localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
}

export function clearStoredSessionId(): void {
  localStorage.removeItem(SESSION_STORAGE_KEY);
}
