import { useEffect, useState } from "react";

export function useWebSocket(url: string) {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!url) {
      return;
    }

    const socket = new WebSocket(url);
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);

    return () => {
      socket.close();
    };
  }, [url]);

  return { connected };
}
