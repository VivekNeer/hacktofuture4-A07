"use client";
import { useEffect, useState } from "react";
import { TimelineEvent } from "@/lib/types";
import { api } from "@/lib/api";
import Spinner from "@/components/ui/Spinner";

interface Props {
  incidentId: string;
}

export default function TimelinePanel({ incidentId }: Props) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .getTimeline(incidentId)
      .then((res) => setEvents(res.events))
      .finally(() => setLoading(false));
  }, [incidentId]);

  if (loading) {
    return <Spinner />;
  }

  return (
    <section className="timeline-panel panel">
      <h3 className="section-title">Timeline</h3>
      <ul className="timeline-list">
        {events.map((event, idx) => (
          <li key={idx} className="timeline-item">
            <div>{event.timestamp}</div>
            <div>
              {event.status} · {event.actor}
            </div>
            <div>{event.note}</div>
          </li>
        ))}
      </ul>
    </section>
  );
}
