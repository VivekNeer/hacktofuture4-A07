import { ConnectionBadge } from "../components/ConnectionBadge";
import { type Incident } from "../lib/types";

const mockIncidents: Incident[] = [
  {
    incidentId: "inc-001",
    service: "payment-api",
    status: "open",
    failureClass: "resource",
    createdAt: new Date().toISOString(),
  },
];

export default function HomePage() {
  return (
    <main style={{ padding: "24px", fontFamily: "ui-sans-serif, system-ui" }}>
      <h1 style={{ marginBottom: "12px" }}>RanOutOfTokens Ops Console</h1>
      <ConnectionBadge connected={true} />

      <section style={{ marginTop: "24px" }}>
        <h2>Incident Feed</h2>
        <ul>
          {mockIncidents.map((inc) => (
            <li key={inc.incidentId}>
              {inc.incidentId} | {inc.service} | {inc.status}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
