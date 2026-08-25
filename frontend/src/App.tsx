/** Circuit Lens v1.6 — Optical Bench application shell, intentionally dark and camera-first. */
import ErrorBoundary from "./components/ErrorBoundary";
import Home from "./pages/Home";

function App() {
  return (
    <ErrorBoundary>
      <Home />
    </ErrorBoundary>
  );
}

export default App;
