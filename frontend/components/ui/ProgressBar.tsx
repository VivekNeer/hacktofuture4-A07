interface Props {
  value: number;
  label?: string;
}

export default function ProgressBar({ value, label }: Props) {
  const safe = Math.max(0, Math.min(1, value));

  return (
    <div className="progress-wrap" aria-label={label ?? "progress"}>
      {label && <div>{label}</div>}
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${safe * 100}%` }} />
      </div>
    </div>
  );
}
