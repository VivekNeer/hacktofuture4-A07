"use client";
import { useState, useEffect, useCallback } from "react";
import { IncidentListItem } from "@/lib/types";
import { api } from "@/lib/api";

export function useIncidents() {
  const [incidents, setIncidents] = useState<IncidentListItem[]>([]);

  const reload = useCallback(() => {
    api.listIncidents({ limit: 50 }).then((res) => setIncidents(res.incidents));
  }, []);

  useEffect(() => {
    reload();
    const timer = setInterval(reload, 30_000);
    return () => clearInterval(timer);
  }, [reload]);

  return { incidents, reload };
}
