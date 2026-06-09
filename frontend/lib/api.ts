import type {
  ChatResponse,
  ChecklistEnvelopeResponse,
  CreateSessionResponse,
  HealthResponse,
  MoveInPlan,
  ProductRecommendationsEnvelopeResponse,
  RuntimeMetricsResponse,
  SessionSnapshotResponse,
  SessionSummary,
  TimelineEnvelopeResponse,
} from "@/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const SESSION_NOT_FOUND = "Session not found.";
const NO_PLAN = "No plan has been generated for this session yet.";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function getApiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.detail ?? error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong. Please try again.";
}

export function isNetworkError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 0;
}

export function isSessionNotFound(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    error.status === 404 &&
    (error.detail === SESSION_NOT_FOUND ||
      error.message.includes("Session not found"))
  );
}

export function isNoPlanError(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    error.status === 404 &&
    (error.detail === NO_PLAN ||
      error.message.includes("No plan has been generated"))
  );
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError(
      "Cannot reach the backend. Is it running on port 8000?",
      0,
    );
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // ignore parse errors
    }
    throw new ApiError(detail, res.status, detail);
  }

  return (await res.json()) as T;
}

export function health(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function createSession(title?: string): Promise<CreateSessionResponse> {
  return request<CreateSessionResponse>("/api/v1/sessions", {
    method: "POST",
    body: title ? JSON.stringify({ title }) : undefined,
  });
}

export function listSessions(): Promise<SessionSummary[]> {
  return request<SessionSummary[]>("/api/v1/sessions");
}

export function getSession(sessionId: string): Promise<SessionSnapshotResponse> {
  return request<SessionSnapshotResponse>(`/api/v1/sessions/${sessionId}`);
}

export function sendChat(
  sessionId: string,
  message: string,
): Promise<ChatResponse> {
  return request<ChatResponse>("/api/v1/chat", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, message }),
  });
}

export function getPlan(sessionId: string): Promise<MoveInPlan> {
  return request<MoveInPlan>(`/api/v1/sessions/${sessionId}/plan`);
}

export function getChecklist(
  sessionId: string,
): Promise<ChecklistEnvelopeResponse> {
  return request<ChecklistEnvelopeResponse>(
    `/api/v1/sessions/${sessionId}/checklist`,
  );
}

export function getProducts(
  sessionId: string,
): Promise<ProductRecommendationsEnvelopeResponse> {
  return request<ProductRecommendationsEnvelopeResponse>(
    `/api/v1/sessions/${sessionId}/products`,
  );
}

export function getTimeline(
  sessionId: string,
): Promise<TimelineEnvelopeResponse> {
  return request<TimelineEnvelopeResponse>(
    `/api/v1/sessions/${sessionId}/timeline`,
  );
}

export function getRuntimeMetrics(): Promise<RuntimeMetricsResponse> {
  return request<RuntimeMetricsResponse>("/api/v1/metrics/runtime");
}
