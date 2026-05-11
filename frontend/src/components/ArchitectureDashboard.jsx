import { memo, useEffect, useState } from "react";
import { getAnalytics } from "../api/api";

const FEATURES = [
  { label: "Semantic Search",     icon: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" },
  { label: "Graph Ranking",       icon: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" },
  { label: "Symbol Registry",     icon: "M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" },
  { label: "Dependency Analysis", icon: "M13 10V3L4 14h7v7l9-11h-7z" },
];

function ArchitectureDashboard({ chatId, currentRepo }) {
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    if (!currentRepo || !chatId) return;
    let dead = false;
    (async () => {
      try {
        const d = await getAnalytics(chatId);
        if (!dead) setAnalytics(d);
      } catch (e) { console.error(e); }
    })();
    return () => { dead = true; };
  }, [currentRepo, chatId]);

  if (!currentRepo) return null;

  return (
    <div className="card" style={{ overflow: "hidden" }}>
      {/* Header */}
      <div style={{
        padding: "18px 24px",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 16,
      }}>
        <div style={{ minWidth: 0 }}>
          <h3 style={{ fontSize: 17, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4, letterSpacing: "-0.01em" }}>
            Repository Overview
          </h3>
          <p style={{ fontSize: 12, color: "var(--text-muted)", wordBreak: "break-all", lineHeight: 1.5 }}>
            {currentRepo}
          </p>
        </div>
        <span className="badge badge-green" style={{ flexShrink: 0 }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--green)", display: "inline-block" }} />
          Indexed
        </span>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", borderBottom: "1px solid var(--border)" }}>
        {analytics ? (
          [
            { label: "Indexed Files", value: analytics.total_files },
            { label: "Code Chunks",   value: analytics.total_chunks },
            { label: "Symbols",       value: analytics.total_symbols },
          ].map(({ label, value }, i) => (
            <div key={label} style={{
              padding: "20px 24px",
              borderRight: i < 2 ? "1px solid var(--border)" : "none",
            }}>
              <div className="label" style={{ marginBottom: 8 }}>{label}</div>
              <div style={{ fontSize: 30, fontWeight: 800, color: "var(--text-primary)", fontVariantNumeric: "tabular-nums", lineHeight: 1, letterSpacing: "-0.02em" }}>
                {value ?? "—"}
              </div>
            </div>
          ))
        ) : (
          [0, 1, 2].map((i) => (
            <div key={i} style={{ padding: "20px 24px", borderRight: i < 2 ? "1px solid var(--border)" : "none" }}>
              <div className="skeleton" style={{ height: 10, width: "55%", marginBottom: 10 }} />
              <div className="skeleton" style={{ height: 26, width: "40%" }} />
            </div>
          ))
        )}
      </div>

      {/* Features */}
      <div style={{ padding: "14px 24px", display: "flex", flexWrap: "wrap", gap: 8 }}>
        {FEATURES.map(({ label, icon }) => (
          <div key={label} style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "5px 11px",
            background: "var(--bg-muted)",
            border: "1px solid var(--border)",
            borderRadius: "var(--r)",
            fontSize: 13,
            fontWeight: 500,
            color: "var(--text-secondary)",
          }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d={icon}/>
            </svg>
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}

export default memo(ArchitectureDashboard);
