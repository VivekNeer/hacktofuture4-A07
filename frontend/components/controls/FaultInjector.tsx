"use client";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface Props {
  onInjected: () => void;
}

export default function FaultInjector({ onInjected }: Props) {
  const [scenarios, setScenarios] = useState<{ scenario_id: string; name: string }[]>([]);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listScenarios().then(setScenarios);
  }, []);

  const inject = async () => {
    if (!selected) return;
    setLoading(true);
    try {
      await api.injectFault(selected);
      onInjected();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fault-injector">
      <select
        id="scenario-select"
        className="scenario-select"
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
        aria-label="Select fault scenario"
      >
        <option value="">Select scenario...</option>
        {scenarios.map((s) => (
          <option key={s.scenario_id} value={s.scenario_id}>
            {s.name}
          </option>
        ))}
      </select>
      <button
        id="inject-fault-btn"
        className="btn-inject"
        onClick={inject}
        disabled={loading || !selected}
      >
        {loading ? "Injecting..." : "Inject Fault"}
      </button>
    </div>
  );
}
