import { memo, useCallback, useMemo, useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

const EXT_LANG = {
  ".py": "python", ".js": "javascript", ".jsx": "jsx",
  ".ts": "typescript", ".tsx": "tsx", ".java": "java",
  ".go": "go", ".rs": "rust", ".md": "markdown",
  ".json": "json", ".css": "css", ".html": "markup",
};

function langFromPath(fp) {
  if (!fp) return "text";
  const dot = fp.lastIndexOf(".");
  return dot < 0 ? "text" : (EXT_LANG[fp.slice(dot).toLowerCase()] || "text");
}

const SHL_STYLE = {
  margin: 0,
  fontSize: "12px",
  background: "#f8fafc",
  maxHeight: 300,
  borderRadius: 0,
};

function SourceCard({ result, onInspectFile }) {
  const [open, setOpen] = useState(false);
  const lang = useMemo(() => langFromPath(result.file_path), [result.file_path]);

  const handleInspect = useCallback((e) => {
    e.stopPropagation();
    onInspectFile(result.file_path);
  }, [onInspectFile, result.file_path]);

  const scoreJson = useMemo(() => {
    const b = result.retrieval_metadata?.score_breakdown;
    return b ? JSON.stringify(b, null, 2) : null;
  }, [result.retrieval_metadata]);

  const score = result.retrieval_metadata?.final_score;
  const scoreStr = typeof score === "number" ? score.toFixed(3) : score;

  return (
    <div style={{
      background: "var(--bg)",
      border: "1px solid var(--border)",
      borderRadius: "var(--r-md)",
      overflow: "hidden",
      boxShadow: "var(--shadow-sm)",
    }}>
      {/* Header row */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          padding: "11px 14px",
          background: "none",
          border: "none",
          cursor: "pointer",
          textAlign: "left",
        }}
      >
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
              {result.symbol_name || "—"}
            </span>
            {result.chunk_type && <span className="tag">{result.chunk_type}</span>}
            {scoreStr && <span className="badge badge-indigo" style={{ fontSize: 10 }}>{scoreStr}</span>}
          </div>
          <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {result.file_path}
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
          {onInspectFile && result.file_path && (
            <button type="button" onClick={handleInspect} className="btn btn-ghost" style={{ padding: "3px 8px", fontSize: 11 }}>
              Inspect
            </button>
          )}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            style={{ transition: "transform 0.15s", transform: open ? "rotate(180deg)" : "none", flexShrink: 0 }}>
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
      </button>

      {open && (
        <div style={{ borderTop: "1px solid var(--border)" }}>
          {/* Meta */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", borderBottom: "1px solid var(--border)" }}>
            <div style={{ padding: "10px 14px", borderRight: "1px solid var(--border)" }}>
              <div className="label" style={{ marginBottom: 4 }}>Retrieval Source</div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                {result.retrieval_metadata?.retrieval_source || "—"}
              </div>
            </div>
            <div style={{ padding: "10px 14px" }}>
              <div className="label" style={{ marginBottom: 4 }}>Final Score</div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)", fontVariantNumeric: "tabular-nums" }}>
                {scoreStr || "—"}
              </div>
            </div>
          </div>

          {scoreJson && (
            <div style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)" }}>
              <div className="label" style={{ marginBottom: 6 }}>Score Breakdown</div>
              <pre style={{
                fontSize: 11,
                color: "var(--text-secondary)",
                background: "var(--bg-subtle)",
                border: "1px solid var(--border)",
                borderRadius: "var(--r-sm)",
                padding: "8px 10px",
                overflowX: "auto",
                fontFamily: "'JetBrains Mono', ui-monospace, monospace",
              }}>
                {scoreJson}
              </pre>
            </div>
          )}

          {result.content && (
            <div>
              <div style={{ padding: "8px 14px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span className="label">Code Preview</span>
                <span className="tag">{lang}</span>
              </div>
              <div style={{ maxHeight: 300, overflowY: "auto" }}>
                <SyntaxHighlighter language={lang} style={oneLight} customStyle={SHL_STYLE}>
                  {result.content}
                </SyntaxHighlighter>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default memo(SourceCard);
