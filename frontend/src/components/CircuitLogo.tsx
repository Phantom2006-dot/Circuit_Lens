/** Circuit Lens v1.6 — Optical Bench brand mark. */
type CircuitLogoProps = {
  className?: string;
};

export function CircuitLogo({ className = "" }: CircuitLogoProps) {
  return (
    <img
      className={className}
      src="/assets/circuit-lens-logo.png"
      alt="Circuit Lens"
    />
  );
}
