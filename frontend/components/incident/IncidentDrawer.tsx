"use client";
import { useEffect, useState } from "react";
import { IncidentDetail } from "@/lib/types";
import { api } from "@/lib/api";
import Spinner from "@/components/ui/Spinner";
import SignalPanel from "./SignalPanel";
import DiagnosisPanel from "./DiagnosisPanel";
import PlannerPanel from "./PlannerPanel";
import ExecutorPanel from "./ExecutorPanel";
import TimelinePanel from "./TimelinePanel";
import TokenCostPanel from "./TokenCostPanel";

interface Props {
  incidentId: string;
  onClose: () => void;
}

export default function IncidentDrawer({ incidentId, onClose }: Props) {
  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "signals" | "diagnosis" | "plan" | "execution" | "timeline" | "cost"
  >("signals");

  useEffect(() => {
    setLoading(true);
    api
      .getIncident(incidentId)
      .then(setIncident)
      .finally(() => setLoading(false));
  }, [incidentId]);

  const TABS = ["signals", "diagnosis", "plan", "execution", "timeline", "cost"] as const;

  return (
    <div className="drawer-overlay" onClick={onClose} aria-modal="true" role="dialog">
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div>
            <h2 className="drawer-title">{incidentId}</h2>
            {incident && (
              <span className="drawer-subtitle">
                {incident.service} · {incident.namespace} · {incident.failure_class}
              </span>
            )}
          </div>
          <button
            id="close-drawer-btn"
            className="close-btn"
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <nav className="drawer-tabs" role="tablist">
          {TABS.map((tab) => (
            <button
              key={tab}
              id={`tab-${tab}`}
              role="tab"
              aria-selected={activeTab === tab}
              className={`tab-btn ${activeTab === tab ? "active" : ""}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>

        <div className="drawer-body">
          {loading && <Spinner />}
          {!loading && incident && (
            <>
              {activeTab === "signals" && <SignalPanel snapshot={incident.snapshot} />}
              {activeTab === "diagnosis" && (
                <DiagnosisPanel
                  diagnosis={incident.diagnosis}
                  incidentId={incidentId}
                  onRefresh={() => api.getIncident(incidentId).then(setIncident)}
                />
              )}
              {activeTab === "plan" && (
                <PlannerPanel
                  plan={incident.plan}
                  incidentId={incidentId}
                  onRefresh={() => api.getIncident(incidentId).then(setIncident)}
                />
              )}
              {activeTab === "execution" && (
                <ExecutorPanel
                  execution={incident.execution}
                  incidentId={incidentId}
                  onRefresh={() => api.getIncident(incidentId).then(setIncident)}
                />
              )}
              {activeTab === "timeline" && <TimelinePanel incidentId={incidentId} />}
              {activeTab === "cost" && <TokenCostPanel incidentId={incidentId} />}
            </>
          )}
        </div>
      </aside>
    </div>
  );
}
