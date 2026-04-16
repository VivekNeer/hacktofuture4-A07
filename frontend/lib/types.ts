export type IncidentStatus = "open" | "investigating" | "resolved";

export interface Incident {
  incidentId: string;
  service: string;
  status: IncidentStatus;
  failureClass?: string;
  createdAt: string;
}
