import { IncidentSnapshot } from "@/lib/types";

interface Props {
  snapshot: IncidentSnapshot | null;
}

export default function SignalPanel({ snapshot }: Props) {
  if (!snapshot) {
    return (
      <section className="signal-panel panel-empty">
        <h3 className="section-title">Observation Signals</h3>
        <p>No snapshot is available yet for this incident.</p>
      </section>
    );
  }

  return (
    <section className="signal-panel panel">
      <h3 className="section-title">Observation Signals</h3>
      <div className="signal-grid">
        <div className="signal-item">
          <strong>Alert</strong>
          <div>{snapshot.alert}</div>
        </div>
        <div className="signal-item">
          <strong>Service / Pod</strong>
          <div>
            {snapshot.service} / {snapshot.pod}
          </div>
        </div>
        <div className="signal-item">
          <strong>CPU</strong>
          <div>{snapshot.metrics.cpu}</div>
        </div>
        <div className="signal-item">
          <strong>Memory</strong>
          <div>{snapshot.metrics.memory}</div>
        </div>
        <div className="signal-item">
          <strong>Restarts</strong>
          <div>{snapshot.metrics.restarts}</div>
        </div>
        <div className="signal-item">
          <strong>Latency Δ</strong>
          <div>{snapshot.metrics.latency_delta}</div>
        </div>
        <div className="signal-item">
          <strong>Failure Class</strong>
          <div>{snapshot.failure_class}</div>
        </div>
        <div className="signal-item">
          <strong>Monitor Confidence</strong>
          <div>{Math.round(snapshot.monitor_confidence * 100)}%</div>
        </div>
      </div>
    </section>
  );
}
