import {
  DiagnosisPayload,
  ExecutorResult,
  IncidentDetail,
  IncidentListItem,
  PlannerOutput,
  TimelineEvent,
  VerificationOutput,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  healthz: () => apiFetch<{ status: string; version: string }>("/healthz"),

  listIncidents: (params?: { status?: string; limit?: number }) =>
    apiFetch<{ total: number; incidents: IncidentListItem[] }>(
      `/incidents/?${new URLSearchParams(params as any)}`
    ),

  getIncident: (id: string) => apiFetch<IncidentDetail>(`/incidents/${id}`),

  getTimeline: (id: string) =>
    apiFetch<{ incident_id: string; events: TimelineEvent[] }>(`/incidents/${id}/timeline`),

  injectFault: (scenario_id: string) =>
    apiFetch<{ incident_id: string; status: string }>("/inject-fault", {
      method: "POST",
      body: JSON.stringify({ scenario_id }),
    }),

  listScenarios: () =>
    apiFetch<{ scenario_id: string; name: string; failure_class: string }[]>("/scenarios"),

  diagnose: (id: string) =>
    apiFetch<DiagnosisPayload>(`/incidents/${id}/diagnose`, { method: "POST" }),

  plan: (id: string) => apiFetch<PlannerOutput>(`/incidents/${id}/plan`, { method: "POST" }),

  approve: (id: string, action_index: number, approved: boolean, note?: string) =>
    apiFetch<{ status: string; message: string }>(`/incidents/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ action_index, approved, operator_note: note ?? "" }),
    }),

  execute: (id: string) =>
    apiFetch<ExecutorResult>(`/incidents/${id}/execute`, { method: "POST" }),

  verify: (id: string) =>
    apiFetch<VerificationOutput>(`/incidents/${id}/verify`, { method: "POST" }),

  getCostReport: (id?: string) =>
    apiFetch<import("./types").CostReport>(`/cost-report${id ? `?incident_id=${id}` : ""}`),
};
