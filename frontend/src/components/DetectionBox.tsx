/**
 * Circuit Lens v1.6 — Optical Bench detection overlay.
 * Brackets, micro-labels, and focus states maintain the calibrated instrument feel.
 */
import type { CircuitDetection } from "@/lib/circuitDetections";

type DetectionBoxProps = {
  detection: CircuitDetection;
  active: boolean;
  onSelect: (id: string) => void;
};

export function DetectionBox({ detection, active, onSelect }: DetectionBoxProps) {
  const { box } = detection;

  return (
    <button
      type="button"
      className={`detection-box ${active ? "is-active" : ""}`}
      aria-label={`Inspect ${detection.ref}, ${detection.kind}`}
      onClick={() => onSelect(detection.id)}
      style={{
        left: `${box.x}%`,
        top: `${box.y}%`,
        width: `${box.width}%`,
        height: `${box.height}%`,
      }}
    >
      <span className="detection-bracket detection-bracket--tl" />
      <span className="detection-bracket detection-bracket--tr" />
      <span className="detection-bracket detection-bracket--bl" />
      <span className="detection-bracket detection-bracket--br" />
      <span className="detection-label">
        <strong>{detection.ref}</strong>
        <span>{detection.kind}</span>
        <em>{Math.round(detection.confidence * 100)}%</em>
      </span>
    </button>
  );
}
