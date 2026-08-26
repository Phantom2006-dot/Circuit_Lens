/**
 * Circuit Lens v1.6 — Optical Bench design.
 * A dark, asymmetric scientific-instrument workspace where the live viewport
 * is primary, Circuit Green communicates confirmed signal, and utility panels
 * use calibrated ticks rather than generic rounded-card patterns.
 */
import { CircuitLogo } from "@/components/CircuitLogo";
import { DetectionBox } from "@/components/DetectionBox";
import {
  analyzeCircuitTopology,
  getReferenceForFamily,
  hasInferenceApi,
  identifyHardware,
  inferCircuitImage,
  inspectCircuitFrame,
  type ComponentReference,
  type HardwareConclusion,
  type TopologyAnalysis,
  type CircuitDetection,
} from "@/lib/circuitDetections";
import {
  Aperture,
  Camera,
  ChevronDown,
  CircleHelp,
  ClipboardCheck,
  Crosshair,
  Expand,
  Flashlight,
  Focus,
  Gauge,
  History,
  Info,
  Layers3,
  ListFilter,
  LoaderCircle,
  Menu,
  MoreHorizontal,
  MoveUpRight,
  Pause,
  ScanLine,
  Settings2,
  Sparkles,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

const NAVIGATION = [
  { label: "Inspect", icon: Aperture, active: true },
  { label: "Sessions", icon: History },
  { label: "Models", icon: Layers3 },
  { label: "Settings", icon: Settings2 },
];

const FAMILY_FILTERS = [
  { key: "all", label: "All" },
  { key: "passive", label: "Passives" },
  { key: "semiconductor", label: "Semiconductors" },
  { key: "power", label: "Power" },
  { key: "interconnect", label: "Connectors" },
  { key: "controller_module", label: "Modules" },
  { key: "sensor_module", label: "Sensors" },
  { key: "electromechanical", label: "Switches & motion" },
  { key: "display_support", label: "Displays" },
  { key: "other", label: "Other" },
] as const;

type InspectionMode = "component" | "board";

const INSPECTION_MODES: { id: InspectionMode; label: string; summary: string; detail: string; icon: typeof Crosshair }[] = [
  { id: "component", label: "Analyze components", summary: "Mark & classify parts", detail: "Find and classify component candidates and their locations in the current frame.", icon: Crosshair },
  { id: "board", label: "Identify circuit board", summary: "Name the board", detail: "Use the full frame and component context to rank the board or module identity.", icon: Sparkles },
];

function ConfidenceRing({ confidence }: { confidence: number }) {
  const dash = 96 - confidence * 96;
  return (
    <div className="confidence-ring" aria-label={`${Math.round(confidence * 100)} percent confidence`}>
      <svg viewBox="0 0 36 36" aria-hidden="true">
        <path className="confidence-ring__track" d="M18 2.0845a15.9155 15.9155 0 0 1 0 31.831a15.9155 15.9155 0 0 1 0-31.831" />
        <path
          className="confidence-ring__value"
          d="M18 2.0845a15.9155 15.9155 0 0 1 0 31.831a15.9155 15.9155 0 0 1 0-31.831"
          style={{ strokeDasharray: `${96 - dash} ${dash}` }}
        />
      </svg>
      <span>{Math.round(confidence * 100)}</span>
    </div>
  );
}

export default function Home() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameCanvasRef = useRef<HTMLCanvasElement>(null);
  const inferenceInFlightRef = useRef(false);
  const [detections, setDetections] = useState<CircuitDetection[]>([]);
  const [selectedId, setSelectedId] = useState("q2");
  const [isScanning, setIsScanning] = useState(true);
  const [cameraState, setCameraState] = useState<"demo" | "connecting" | "live" | "blocked">("demo");
  const [showGuidance, setShowGuidance] = useState(false);
  const [isNavOpen, setIsNavOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [objectQuery, setObjectQuery] = useState("");
  const [inspectionMode, setInspectionMode] = useState<InspectionMode>("component");
  const [inferenceState, setInferenceState] = useState<"demo" | "waiting" | "sampling" | "live" | "error">("demo");
  const [reference, setReference] = useState<ComponentReference | null>(null);
  const [topology, setTopology] = useState<TopologyAnalysis | null>(null);
  const [topologyState, setTopologyState] = useState<"idle" | "analyzing" | "ready" | "error">("idle");
  const [hardware, setHardware] = useState<HardwareConclusion | null>(null);
  const [hardwareState, setHardwareState] = useState<"idle" | "analyzing" | "ready" | "error">("idle");
  const selected = detections.find((detection) => detection.id === selectedId) ?? detections[0];

  useEffect(() => {
    let mounted = true;
    inspectCircuitFrame().then((result) => {
      if (mounted) setDetections(result);
    });

    return () => {
      mounted = false;
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  useEffect(() => {
    if (cameraState !== "live" || !isScanning) return;
    if (!hasInferenceApi()) {
      setInferenceState("waiting");
      return;
    }

    let active = true;
    const submitFrame = async () => {
      const video = videoRef.current;
      const canvas = frameCanvasRef.current;
      if (!video || !canvas || !video.videoWidth || inferenceInFlightRef.current) return;
      inferenceInFlightRef.current = true;
      setInferenceState("sampling");
      try {
        const longEdge = 640;
        const ratio = longEdge / Math.max(video.videoWidth, video.videoHeight);
        canvas.width = Math.round(video.videoWidth * ratio);
        canvas.height = Math.round(video.videoHeight * ratio);
        const context = canvas.getContext("2d");
        if (!context) return;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        const frame = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.82));
        if (!frame) throw new Error("The camera frame could not be encoded.");
        if (inspectionMode === "board") {
          setHardwareState("analyzing");
          const conclusion = await identifyHardware(frame);
          if (!active) return;
          setHardware(conclusion);
          setDetections(conclusion.components);
          setSelectedId((current) => conclusion.components.some((item) => item.id === current) ? current : (conclusion.components[0]?.id ?? current));
          setHardwareState("ready");
          setInferenceState("live");
          return;
        }
        const nextDetections = await inferCircuitImage(frame);
        if (!active) return;
        setDetections(nextDetections);
        setSelectedId((current) => nextDetections.some((item) => item.id === current) ? current : (nextDetections[0]?.id ?? current));
        setInferenceState("live");
      } catch {
        if (active) setInferenceState("error");
      } finally {
        inferenceInFlightRef.current = false;
      }
    };

    void submitFrame();
    const timer = window.setInterval(() => void submitFrame(), inspectionMode === "component" ? 1250 : 3000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [cameraState, inspectionMode, isScanning]);

  useEffect(() => {
    if (!selected || !hasInferenceApi()) {
      setReference(null);
      return;
    }
    let active = true;
    getReferenceForFamily(selected.kind).then((record) => {
      if (active) setReference(record);
    });
    return () => { active = false; };
  }, [selected?.kind]);

  const visibleDetections = detections.filter((detection) => {
    const inFamily = activeFilter === "all" || detection.family === activeFilter;
    const searchable = `${detection.ref} ${detection.kind} ${detection.family} ${detection.value}`.toLowerCase();
    return inFamily && searchable.includes(objectQuery.trim().toLowerCase());
  });

  const startCamera = async () => {
    if (cameraState === "live") return;
    setCameraState("connecting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraState("live");
      setIsScanning(true);
      setInferenceState(hasInferenceApi() ? "sampling" : "waiting");
    } catch {
      setCameraState("blocked");
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraState("demo");
    setIsScanning(false);
    setInferenceState("demo");
  };

  const analyzeTopology = async () => {
    const video = videoRef.current;
    const canvas = frameCanvasRef.current;
    if (!video || !canvas || !video.videoWidth) {
      setShowGuidance(true);
      return;
    }
    setTopologyState("analyzing");
    try {
      const scale = 640 / Math.max(video.videoWidth, video.videoHeight);
      canvas.width = Math.round(video.videoWidth * scale);
      canvas.height = Math.round(video.videoHeight * scale);
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Canvas unavailable");
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const frame = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
      if (!frame) throw new Error("Frame encoding failed");
      setTopology(await analyzeCircuitTopology(frame));
      setTopologyState("ready");
    } catch {
      setTopologyState("error");
    }
  };

  const identifyBoard = async () => {
    const video = videoRef.current;
    const canvas = frameCanvasRef.current;
    if (!video || !canvas || !video.videoWidth) {
      setShowGuidance(true);
      return;
    }
    setHardwareState("analyzing");
    try {
      const scale = 640 / Math.max(video.videoWidth, video.videoHeight);
      canvas.width = Math.round(video.videoWidth * scale);
      canvas.height = Math.round(video.videoHeight * scale);
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Canvas unavailable");
      context.drawImage(video, 0, 0, canvas.width, canvas.height);
      const frame = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
      if (!frame) throw new Error("Frame encoding failed");
      const conclusion = await identifyHardware(frame);
      setHardware(conclusion);
      setDetections(conclusion.components);
      setSelectedId((current) => conclusion.components.some((item) => item.id === current) ? current : (conclusion.components[0]?.id ?? current));
      setHardwareState("ready");
    } catch {
      setHardwareState("error");
    }
  };

  const runFocusedAnalysis = () => {
    if (inspectionMode === "board") {
      void identifyBoard();
      return;
    }
    if (cameraState !== "live") void startCamera();
  };

  const statusLabel = cameraState === "live" ? "Live camera" : cameraState === "connecting" ? "Connecting" : cameraState === "blocked" ? "Camera blocked" : "Demo feed";
  const activeMode = INSPECTION_MODES.find((mode) => mode.id === inspectionMode)!;
  const ModeIcon = activeMode.icon;
  const inferenceLabel = inferenceState === "live" ? `${inspectionMode === "component" ? "COMPONENT" : "BOARD"} LIVE` : inferenceState === "sampling" ? `SAMPLING ${inspectionMode.toUpperCase()}` : inferenceState === "waiting" ? "API NOT CONFIGURED" : inferenceState === "error" ? "RETRYING" : `${inspectionMode === "component" ? "COMPONENT" : "BOARD"} READY`;

  return (
    <main className="app-shell">
      <header className="topbar">
        <button className="mobile-menu" onClick={() => setIsNavOpen(true)} aria-label="Open workspace navigation">
          <Menu size={19} />
        </button>
        <a className="brand" href="#top" aria-label="Circuit Lens home">
          <span className="brand__mark"><CircuitLogo className="brand__logo" /><span className="brand__mark-core" /></span>
          <span className="brand__type">CIRCUIT<span>LENS</span></span>
          <span className="brand__version">v1.6</span>
        </a>
        <div className="topbar__center">
          <span className="eyebrow">ACTIVE SESSION</span>
          <strong>Bench A / Board 07</strong>
          <ChevronDown size={15} />
        </div>
        <div className="topbar__actions">
          <button className="icon-button" onClick={() => setShowGuidance(true)} aria-label="Open guidance"><CircleHelp size={18} /></button>
          <button className="avatar" aria-label="User profile">MO</button>
        </div>
      </header>

      <aside className={`side-rail ${isNavOpen ? "side-rail--open" : ""}`} aria-label="Workspace navigation">
        <div className="side-rail__head">
          <span>WORKSPACE</span>
          <button className="side-rail__close" onClick={() => setIsNavOpen(false)} aria-label="Close navigation"><X size={17} /></button>
        </div>
        <nav className="side-rail__nav">
          {NAVIGATION.map(({ label, icon: Icon, active }) => (
            <button
              key={label}
              className={`rail-item ${active ? "rail-item--active" : ""}`}
              onClick={() => label !== "Inspect" && setShowGuidance(true)}
            >
              <Icon size={18} strokeWidth={1.7} />
              <span>{label}</span>
              {active && <i />}
            </button>
          ))}
        </nav>
        <div className="side-rail__footer">
          <div className="model-chip"><Sparkles size={14} /><span>MODEL</span><b>Edge 4.2</b></div>
          <button onClick={() => setShowGuidance(true)} className="rail-user"><span className="rail-user__avatar">MO</span><span><b>Marcus O.</b><small>Field engineer</small></span><MoreHorizontal size={17} /></button>
        </div>
      </aside>

      <section className="workspace" id="top">
        <div className="workspace__heading">
          <div>
            <p className="eyebrow eyebrow--signal"><span /> CHOOSE ANALYSIS</p>
            <h1>{inspectionMode === "component" ? "Component analysis / Board 07" : "Circuit-board identification / Board 07"}</h1>
            <p className="workspace__intro">{activeMode.detail} Position the board under even light before beginning a focused pass.</p>
            <div className="inspection-mode-selector" role="tablist" aria-label="Choose component or circuit-board analysis">
              {INSPECTION_MODES.map((mode) => {
                const Icon = mode.icon;
                return <button key={mode.id} role="tab" aria-selected={inspectionMode === mode.id} className={`inspection-mode ${inspectionMode === mode.id ? "inspection-mode--active" : ""}`} onClick={() => setInspectionMode(mode.id)}><Icon size={14} /><span><b>{mode.label}</b><small>{mode.summary}</small></span></button>;
              })}
            </div>
          </div>
          <div className="workspace__heading-actions">
            <button className="secondary-button" onClick={runFocusedAnalysis} disabled={hardwareState === "analyzing"}><ModeIcon size={16} /> {hardwareState === "analyzing" ? "Identifying board" : inspectionMode === "component" ? "Analyze components" : "Identify circuit board"}</button>
            <button className="primary-button" onClick={startCamera} disabled={cameraState === "connecting"}>
              {cameraState === "connecting" ? <LoaderCircle className="spin" size={17} /> : <Camera size={17} />}
              {cameraState === "live" ? "Camera armed" : "Arm camera"}
            </button>
          </div>
        </div>

        <section className="inspection-grid" aria-label="Live circuit inspection workspace">
          <article className="lens-stage">
            <div className="lens-stage__bar">
              <div className="feed-status"><span className={`status-dot ${cameraState === "blocked" ? "status-dot--warn" : ""}`} />{statusLabel}<b className="mode-status">{inspectionMode === "component" ? "Component mode" : "Board mode"}</b></div>
              <div className="feed-meta"><span>1920 × 1080</span><span className="feed-meta__divider" /><span>{isScanning ? "30 FPS" : "PAUSED"}</span></div>
            </div>

            <div className="camera-frame">
              <img className={`demo-board ${cameraState === "live" ? "demo-board--hidden" : ""}`} src="/assets/circuit-lens-live-board.png" alt="Circuit board inspection sample" />
              <video ref={videoRef} className={`camera-feed ${cameraState === "live" ? "camera-feed--visible" : ""}`} playsInline muted />
              <canvas ref={frameCanvasRef} aria-hidden="true" style={{ position: "absolute", width: 1, height: 1, opacity: 0, pointerEvents: "none" }} />
              <div className="frame-shade" />
              <div className="reticle reticle--horizontal" />
              <div className="reticle reticle--vertical" />
              <span className="frame-corner frame-corner--tl" /><span className="frame-corner frame-corner--tr" />
              <span className="frame-corner frame-corner--bl" /><span className="frame-corner frame-corner--br" />
              {isScanning && <span className="scan-line" />}
              <div className="calibration calibration--top"><span>0</span><i /><i /><i /><span>25</span><i /><i /><i /><span>50 mm</span></div>
              <div className="calibration calibration--left"><span>0</span><i /><i /><i /><span>25</span></div>
              {visibleDetections.map((detection) => (
                <DetectionBox key={detection.id} detection={detection} active={detection.id === selectedId} onSelect={setSelectedId} />
              ))}
              <div className="analysis-copy"><span>INFERENCE PASS</span><b>{isScanning ? inferenceLabel : "PAUSED"}</b></div>
              {cameraState === "blocked" && (
                <div className="camera-message"><Flashlight size={20} /><strong>Camera access was not granted.</strong><span>Use the demo feed or allow camera access in your browser to inspect your own board.</span><button onClick={startCamera}>Try camera again</button></div>
              )}
            </div>

            <div className="lens-stage__controls">
              <div className="control-group"><span>Overlay</span><button className="mode-button mode-button--active" aria-label="Show labels"><Crosshair size={16} /></button><button className="mode-button" onClick={() => setShowGuidance(true)} aria-label="Show traces"><ScanLine size={16} /></button><button className="mode-button" onClick={() => setShowGuidance(true)} aria-label="Show values"><Gauge size={16} /></button></div>
              <div className="control-group control-group--end"><button className="text-control" onClick={() => setIsScanning((value) => !value)}>{isScanning ? <Pause size={15} /> : <Focus size={15} />}{isScanning ? "Pause scan" : "Resume scan"}</button><button className="mode-button" onClick={() => setShowGuidance(true)} aria-label="Expand viewport"><Expand size={16} /></button></div>
            </div>
          </article>

          <aside className="inspector-panel" aria-label="Selected component details">
            <div className="panel-title"><div><span className="eyebrow">FOCUS OBJECT</span><h2>{selected?.ref ?? "—"}</h2></div><button className="icon-button icon-button--dark" onClick={() => setShowGuidance(true)} aria-label="More component actions"><MoreHorizontal size={18} /></button></div>
            {selected && (
              <>
                <div className="focus-card">
                  <div className="focus-card__type"><div className="component-symbol component-symbol--transistor"><i /><i /><i /></div><span><b>{selected.kind}</b><small>{selected.value}</small></span></div>
                  <span className={`health-pill health-pill--${selected.health.toLowerCase()}`}>{selected.health}</span>
                </div>
                <div className="confidence-row"><ConfidenceRing confidence={selected.confidence} /><div><span className="eyebrow">MODEL CONFIDENCE</span><b>High correspondence</b><p>{selected.note}</p></div></div>
                <div className="divider-label"><span>INSPECTION NOTES</span></div>
                <div className="signal-map">
                  <div className="signal-map__line"><span className="signal-node signal-node--active" /> <i /> <span className="signal-node" /> <i /> <span className="signal-node" /></div>
                  <div className="signal-map__legend"><span>Input trace</span><span>Component</span><span>Output trace</span></div>
                </div>
                {topology && <div className="topology-card"><span className="eyebrow">CIRCUIT HYPOTHESIS · REVIEW REQUIRED</span><b>{topology.candidate_patterns[0]?.label ?? "Unclassified circuit region"}</b><small>{topology.candidate_links.length} visual links · {topology.candidate_nets.length} candidate nets</small><p>{topology.candidate_patterns[0]?.evidence[0] ?? topology.limitations[0]}</p></div>}
                {hardware && <div className={`hardware-card hardware-card--${hardware.conclusion_status === "candidate_conclusion" ? "ready" : "review"}`}><span className="eyebrow">SMART HARDWARE CONCLUSION</span><b>{hardware.conclusion}</b><small>{hardware.components.length} component candidates · {hardware.board_matches[0] ? `${Math.round(hardware.board_matches[0].confidence * 100)}% board match` : "no trained-board match"}</small><p>{hardware.evidence[0]}</p>{hardware.recognized_markings.length > 0 && <em>Marking read: {hardware.recognized_markings.join(" · ")}</em>}{hardware.board_matches[1] && <em>Alternative: {hardware.board_matches[1].name} · {Math.round(hardware.board_matches[1].confidence * 100)}%</em>}<a href={hardware.board_matches[0]?.source_url} target="_blank" rel="noreferrer">Open board reference <MoveUpRight size={13} /></a></div>}
                {reference && <div className="reference-card"><span className="eyebrow">REFERENCE MATCH</span><b>{reference.manufacturer} · {reference.part_number}</b><small>{reference.package} · {reference.reference_value}</small><a href={reference.datasheet_url} target="_blank" rel="noreferrer">Open source datasheet <MoveUpRight size={13} /></a></div>}
                <button className="detail-link" onClick={() => setShowGuidance(true)}>Open component guide <MoveUpRight size={15} /></button>
              </>
            )}
          </aside>
        </section>

        <section className="detections-section">
          <div className="detections-section__top"><div><p className="eyebrow">INSPECTION RECORD / PASS 01</p><h2>Objects marked in frame <span>{detections.length}</span></h2><p className="object-record-note">All model-recognized objects are retained here—components, modules, connectors, sensors, displays, and controls.</p></div><div className="object-filter-tools"><label className="object-search"><span className="sr-only">Search marked objects</span><input value={objectQuery} onChange={(event) => setObjectQuery(event.target.value)} placeholder="Find a marked object" /></label><div className="filter-row">{FAMILY_FILTERS.map((filter) => <button key={filter.key} className={`filter-pill ${activeFilter === filter.key ? "filter-pill--active" : ""}`} onClick={() => setActiveFilter(filter.key)}>{filter.label}</button>)}<button className="filter-icon" onClick={() => setObjectQuery("")} aria-label="Clear object search"><ListFilter size={17} /></button></div></div></div>
          <div className="detection-list">
            {visibleDetections.map((detection, index) => (
              <button key={detection.id} className={`detection-row ${detection.id === selectedId ? "detection-row--selected" : ""}`} onClick={() => setSelectedId(detection.id)}>
                <span className="detection-row__index">0{index + 1}</span>
                <span className={`detection-row__symbol detection-row__symbol--${detection.kind.toLowerCase()}`}><i /><i /><i /></span>
                <span className="detection-row__name"><b>{detection.ref} · {detection.kind}</b><small>{detection.value}</small></span>
                <span className="detection-row__confidence"><i><em style={{ width: `${detection.confidence * 100}%` }} /></i><b>{Math.round(detection.confidence * 100)}%</b></span>
                <span className={`health-pill health-pill--${detection.health.toLowerCase()}`}>{detection.health}</span>
                <ChevronDown className="row-arrow" size={17} />
              </button>
            ))}
          </div>
        </section>

        <section className="method-strip">
          <div className="method-strip__image"><img src="/assets/circuit-lens-bench-detail.png" alt="Macro circuit board detail" /></div>
          <div className="method-strip__copy"><p className="eyebrow eyebrow--signal"><span /> PYTORCH-READY PIPELINE</p><h2>Camera frames in. Component intelligence out.</h2><p>This web prototype isolates detection behind a portable frame-inspection contract. Connect a PyTorch detector through a secure API now, then reuse the same output schema with a React Native camera adapter later.</p></div>
          <button className="method-strip__link" onClick={() => setShowGuidance(true)}>Inspect frame contract <MoveUpRight size={18} /></button>
        </section>
      </section>

      {showGuidance && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setShowGuidance(false)}>
          <section className="guidance-modal" role="dialog" aria-modal="true" aria-labelledby="guidance-title" onMouseDown={(event) => event.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowGuidance(false)} aria-label="Close guidance"><X size={19} /></button>
            <p className="eyebrow eyebrow--signal"><span /> INSPECTION GUIDE</p>
            <h2 id="guidance-title">Steady framing produces stronger reads.</h2>
            <ol><li><span>01</span> Bring the board into even light and keep the component side unobstructed.</li><li><span>02</span> Select <b>Use camera</b> and grant access when your browser asks.</li><li><span>03</span> Hold the device steady; choose any overlay label for evidence and technical context.</li></ol>
            <div className="modal-note"><Info size={17} /><p>Component candidates, board classification, and topology hypotheses are separate evidence streams. A conclusion is only shown when the board model passes its confidence/margin gate; it still requires visual and electrical review.</p></div>
          </section>
        </div>
      )}
    </main>
  );
}
