export function ConnectionBadge({ connected }: { connected: boolean }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "6px 10px",
        borderRadius: "999px",
        background: connected ? "#dcfce7" : "#fee2e2",
        color: connected ? "#166534" : "#991b1b",
        fontSize: "12px",
        fontWeight: 600,
      }}
    >
      {connected ? "WebSocket Connected" : "WebSocket Disconnected"}
    </span>
  );
}
