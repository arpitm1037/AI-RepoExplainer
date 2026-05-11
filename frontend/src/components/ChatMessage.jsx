import { memo, useMemo } from "react";
import StreamingText from "./StreamingText";
import SourceCard from "./SourceCard";

const MetricBox = ({ label, value }) => (
  <div style={{
    background: "var(--bg-subtle)",
    border: "1px solid var(--border)",
    borderRadius: "var(--r)",
    padding: "8px 12px",
  }}>
    <div className="label" style={{ marginBottom: 3 }}>{label}</div>
    <div style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>{value}</div>
  </div>
);

const PerformanceMetrics = memo(function PerformanceMetrics({ metrics }) {
  if (!metrics) return null;
  return (
    <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
      <span className="label" style={{ display: "block", marginBottom: 8 }}>Performance</span>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
        <MetricBox label="Total"      value={`${metrics.total_time}s`} />
        <MetricBox label="Retrieval"  value={`${metrics.retrieval_time}s`} />
        <MetricBox label="Generation" value={`${metrics.generation_time}s`} />
        <MetricBox label="Cache"      value={metrics.cache_hit ? "Hit ✓" : "Miss"} />
      </div>
    </div>
  );
});

function ChatMessage({ message, onInspectFile }) {
  const isUser = message.role === "user";

  const sources = useMemo(() => {
    if (!message.retrievalResults?.length) return null;
    return (
      <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
          <span className="label">Retrieved Sources</span>
          <span className="badge badge-gray">{message.retrievalResults.length}</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {message.retrievalResults.map((r, i) => (
            <SourceCard key={i} result={r} onInspectFile={onInspectFile} />
          ))}
        </div>
      </div>
    );
  }, [message.retrievalResults, onInspectFile]);

  if (isUser) {
    return (
      <div className="fade-up" style={{ display: "flex", justifyContent: "flex-end" }}>
        <div style={{
          maxWidth: 560,
          background: "var(--accent)",
          borderRadius: "var(--r-lg)",
          borderBottomRightRadius: 4,
          padding: "12px 18px",
          boxShadow: "0 2px 6px rgba(0,0,0,0.18)",
        }}>
          <p style={{ fontSize: 15, lineHeight: 1.65, color: "#fff", whiteSpace: "pre-wrap" }}>
            {message.content}
          </p>
          <p style={{ fontSize: 11, color: "rgba(255,255,255,0.55)", marginTop: 6, textAlign: "right" }}>
            {message.ts}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="fade-up" style={{ display: "flex", justifyContent: "flex-start" }}>
      <div style={{
        width: "100%",
        background: "var(--bg)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-lg)",
        borderBottomLeftRadius: 4,
        padding: "16px 20px",
        boxShadow: "var(--shadow-sm)",
      }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{
              width: 24, height: 24,
              background: "var(--accent)",
              borderRadius: 7,
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0,
            }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="5" y="5" width="6" height="6" rx="1.5" />
              <rect x="13" y="5" width="6" height="6" rx="1.5" opacity="0.85" />
              <rect x="5" y="13" width="6" height="6" rx="1.5" opacity="0.85" />
              <rect x="13" y="13" width="6" height="6" rx="1.5" />
              </svg>
            </div>
            <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>Codebase AI</span>
          </div>
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{message.ts}</span>
        </div>

        <StreamingText content={message.content} />
        <PerformanceMetrics metrics={message.performanceMetrics} />
        {sources}
      </div>
    </div>
  );
}

export default memo(ChatMessage);
