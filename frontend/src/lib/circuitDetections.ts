/**
 * Circuit Lens v1.6 — portable detection contract.
 *
 * Vercel receives only the static React application. Inference is delegated to
 * the Fly.io service via VITE_API_BASE_URL, avoiding any server secret or model
 * binary in the browser bundle. The model-independent output remains suitable
 * for a later React Native camera adapter.
 */
export type CircuitComponentKind = string;

export type CircuitDetection = {
  id: string;
  kind: CircuitComponentKind;
  family: string;
  ref: string;
  confidence: number;
  health: "Verified" | "Likely" | "Review";
  box: { x: number; y: number; width: number; height: number };
  value: string;
  note: string;
};

type DetectionApiResponse = {
  detections: CircuitDetection[];
  model_mode: "demo" | "torchscript";
};

export type ComponentReference = {
  family: string;
  manufacturer: string;
  part_number: string;
  package: string;
  reference_value: string;
  engineering_summary: string;
  specifications: Record<string, string>;
  datasheet_url: string;
  application: string;
};

export type TopologyAnalysis = {
  candidate_links: { confidence: number; evidence: string[] }[];
  candidate_nets: { id: string; terminal_ids: string[]; confidence: number }[];
  candidate_patterns: { label: string; confidence: number; evidence: string[]; requires_review: boolean }[];
  limitations: string[];
};

export type HardwareConclusion = {
  components: CircuitDetection[];
  board_matches: { board_id: string; name: string; family: string; confidence: number; supported_by_trained_model: boolean; component_evidence: string[]; marking_evidence: string[]; visual_evidence: string[]; source_url: string }[];
  conclusion: string;
  conclusion_status: "candidate_conclusion" | "needs_more_evidence";
  evidence: string[];
  recognized_markings: string[];
  next_capture: string;
  board_model_mode: "unavailable" | "torchscript";
};

const FALLBACK_DETECTIONS: CircuitDetection[] = [
  { id: "r7", kind: "Resistor", family: "passive", ref: "R7", confidence: 0.98, health: "Verified", box: { x: 16, y: 53, width: 17, height: 13 }, value: "1 kΩ · 1%", note: "Bias network — trace continuity is visible." },
  { id: "q2", kind: "Transistor", family: "semiconductor", ref: "Q2", confidence: 0.94, health: "Verified", box: { x: 47, y: 33, width: 20, height: 19 }, value: "SOT-23 · NPN", note: "Package geometry is consistent with a switching transistor." },
  { id: "d1", kind: "Diode", family: "semiconductor", ref: "D1", confidence: 0.89, health: "Likely", box: { x: 68, y: 57, width: 18, height: 12 }, value: "Signal diode", note: "Polarity mark is partially occluded by a solder joint." },
  { id: "c4", kind: "Capacitor", family: "passive", ref: "C4", confidence: 0.81, health: "Review", box: { x: 42, y: 68, width: 13, height: 11 }, value: "Ceramic MLCC", note: "Marking is not visible; value requires a closer angle." },
];

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export function hasInferenceApi(): boolean {
  return Boolean(API_BASE_URL);
}

/** Keeps the Vercel preview usable before the Fly.io API is deployed. */
export async function inspectCircuitFrame(): Promise<CircuitDetection[]> {
  if (!API_BASE_URL) return FALLBACK_DETECTIONS;
  try {
    const response = await fetch(`${API_BASE_URL}/v1/detections/demo`, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`Inference service returned ${response.status}`);
    return ((await response.json()) as DetectionApiResponse).detections;
  } catch {
    return FALLBACK_DETECTIONS;
  }
}

/** Upload a captured frame from a canvas or a future React Native camera adapter. */
export async function inferCircuitImage(image: Blob): Promise<CircuitDetection[]> {
  if (!API_BASE_URL) throw new Error("VITE_API_BASE_URL is not configured.");
  const form = new FormData();
  form.append("image", image, "circuit-frame.jpg");
  const response = await fetch(`${API_BASE_URL}/v1/detections/infer`, { method: "POST", body: form });
  if (!response.ok) throw new Error(`Inference failed with ${response.status}`);
  return ((await response.json()) as DetectionApiResponse).detections;
}

/** Retrieves a manufacturer-linked reference card for the detected family. */
export async function getReferenceForFamily(family: CircuitComponentKind): Promise<ComponentReference | null> {
  if (!API_BASE_URL) return null;
  const response = await fetch(`${API_BASE_URL}/v1/catalog/${family.toLowerCase()}`, { headers: { Accept: "application/json" } });
  if (!response.ok) return null;
  const payload = (await response.json()) as { references: ComponentReference[] };
  return payload.references[0] ?? null;
}

/** Requests an evidence graph and candidate circuit patterns from one captured frame. */
export async function analyzeCircuitTopology(image: Blob): Promise<TopologyAnalysis> {
  if (!API_BASE_URL) throw new Error("VITE_API_BASE_URL is not configured.");
  const form = new FormData();
  form.append("image", image, "circuit-topology-frame.jpg");
  const response = await fetch(`${API_BASE_URL}/v1/topology/analyze`, { method: "POST", body: form });
  if (!response.ok) throw new Error(`Topology analysis failed with ${response.status}`);
  return (await response.json()) as TopologyAnalysis;
}

/** Fuses the component detector and IoTKITs board classifier into a ranked conclusion. */
export async function identifyHardware(image: Blob): Promise<HardwareConclusion> {
  if (!API_BASE_URL) throw new Error("VITE_API_BASE_URL is not configured.");
  const form = new FormData();
  form.append("image", image, "hardware-identification-frame.jpg");
  const response = await fetch(`${API_BASE_URL}/v1/hardware/identify`, { method: "POST", body: form });
  if (!response.ok) throw new Error(`Hardware identification failed with ${response.status}`);
  return (await response.json()) as HardwareConclusion;
}
