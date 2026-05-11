import { memo } from "react";

function LoadingMessage() {
  return (
    <div className="fade-up" style={{ display: "flex", justifyContent: "flex-start" }}>
      <div style={{
        background: "var(--bg)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-lg)",
        borderBottomLeftRadius: 4,
        padding: "14px 18px",
        display: "flex",
        alignItems: "center",
        gap: 12,
        boxShadow: "var(--shadow-sm)",
      }}>
        <div style={{
          width: 24, height: 24,
          background: "var(--accent)",
          borderRadius: 7,
          display: "flex", alignItems: "center", justifyContent: "center",
          flexShrink: 0,
        }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
          </svg>
        </div>
        <div className="dot-pulse">
          <span /><span /><span />
        </div>
        <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Thinking…</span>
      </div>
    </div>
  );
}

export default memo(LoadingMessage);
