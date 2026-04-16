import type { Incident } from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchIncidents(): Promise<Incident[]> {
  const response = await fetch(`${BASE_URL}/incidents`);
  if (!response.ok) {
    throw new Error("Failed to fetch incidents");
  }
  return response.json() as Promise<Incident[]>;
}
