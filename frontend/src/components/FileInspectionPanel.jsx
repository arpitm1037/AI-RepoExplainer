import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { getApiErrorMessage, getFileInspect } from "../api/api";

const EXT_LANG = {
  ".py": "python", ".js": "javascript", ".jsx": "jsx",
  ".ts": "typescript", ".tsx": "tsx", ".java": "java",
  ".go": "go", ".rs": "rust", ".md": "markdown",
  ".json": "json", ".css": "css", ".html": "markup",
};

function resolveLang(ext) {
  if (!ext) return "text";
  const k = ext.startsWith(".") ? ext.toLowerCase() : `.${ext.toLowerCase()}`;
  return EXT_LANG[k] || "text";
}

const SHL_STYLE = { margin: 0, fontSize: "12px", background: "#f8fafc" };

function FileInspectionPanel({ chatId, filePath, onClose, onAskAboutFile }) {
  const [data,    setData]    = useState(null);
  const [error,   setError]   = useState(null);
  const [loading, setLoading] = useState(true);

  const lang = useMemo(() => resolveLang(data?.extension), [data?.extension]);

  useEffect(() => {
    if (!chatId) return;
    let dead = false;
    (async () => {
      setLoading(true); setError(null); setData(null);
      try {
        const p = await getFileInspect(chatId, filePath);
        if (!dead) setData(p);
      } catch (e) {
        if (!dead) setError(getApiErrorMessage(e));
      } finally {
        if (!dead) setLoading(false);
      }
    })();
    return () => { dead = true; };
  }, [filePath, chatId]);

  const handleAsk = useCallback(() => {
    onAskAboutFile?.(data?.file_path ?? filePath);
  }, [onAskAboutFile, data?.file_path, filePath]);

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 50,
      display: "flex", alignItems: "center", justifyContent: "center",
      padding: 24,
      background: "rgba(0,0,0,0.45)",
      backdropFilter: "blur(6px)",
    }}>
      <div style={{
        background: "var(--bg)",
        border: "1px solid var(--border)",
        borderRadius: "var(--r-xl)",
        width: "100%", maxWidth: 880,
        maxHeight: "90vh",
        display: "flex", flexDirection: "column",
        overflow: "hidden",
        boxShadow: "var(--shadow-xl)",
      }}>
        {/* Header */}
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16,
          padding: "16px 22px",
          borderBottom: "1px solid var(--border)",
          flexShrink: 0,
        }}>
          <div style={{ minWidth: 0 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)", marginBottom: 3 }}>File Inspection</h3>
            <p style={{ fontSize: 11, color: "var(--text-muted)", wordBreak: "break-all" }}>{filePath}</p>
          </div>
          <button type="button" onClick={onClose} className="btn btn-secondary" style={{ flexShrink: 0, padding: "6px 14px", fontSize: 13 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
            Close
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px 22px", display: "flex", flexDirection: "column", gap: 18 }}>

          {loading && (
            <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "24px 0" }}>
              <span className="spinner" />
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading file…</span>
            </div>
          )}

          {error && (
            <div style={{ background: "var(--red-light)", border: "1px solid #fecaca", borderRadius: "var(--r-md)", padding: "12px 16px", fontSize: 13, color: "var(--red)" }}>
              {error}
            </div>
          )}

          {!loading && data && !error && (
            <>
              {/* Badges */}
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {data.truncated && <span className="badge badge-amber">Truncated</span>}
                <span className="badge badge-gray">{data.extension || "no ext"}</span>
                <span className="badge badge-gray">{data.size_bytes?.toLocaleString()} bytes</span>
              </div>

              {data.summary && (
                <div>
                  <span className="label" style={{ display: "block", marginBottom: 6 }}>Architecture Summary</span>
                  <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7, whiteSpace: "pre-wrap", background: "var(--bg-subtle)", border: "1px solid var(--border)", borderRadius: "var(--r-md)", padding: "12px 14px", maxHeight: 150, overflowY: "auto" }}>
                    {data.summary}
                  </div>
                </div>
              )}

              {data.dependencies?.length > 0 && (
                <div>
                  <span className="label" style={{ display: "block", marginBottom: 6 }}>Import Targets</span>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 5, maxHeight: 80, overflowY: "auto" }}>
                    {data.dependencies.map((d, i) => <span key={`${d}-${i}`} className="tag">{d}</span>)}
                  </div>
                </div>
              )}

              {data.related_files?.length > 0 && (
                <div>
                  <span className="label" style={{ display: "block", marginBottom: 6 }}>Related Files</span>
                  <div style={{ display: "flex", flexDirection: "column", gap: 3, maxHeight: 100, overflowY: "auto" }}>
                    {data.related_files.map((rf) => (
                      <span key={rf} style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "ui-monospace, monospace", wordBreak: "break-all" }}>{rf}</span>
                    ))}
                  </div>
                </div>
              )}

              {data.symbols?.length > 0 && (
                <div>
                  <span className="label" style={{ display: "block", marginBottom: 6 }}>Symbols</span>
                  <div style={{ maxHeight: 180, overflowY: "auto", border: "1px solid var(--border)", borderRadius: "var(--r-md)", overflow: "hidden" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                      <thead>
                        <tr style={{ background: "var(--bg-subtle)" }}>
                          {["Name", "Type", "Lines"].map((h) => (
                            <th key={h} style={{ padding: "8px 12px", textAlign: "left", color: "var(--text-muted)", fontWeight: 600, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em", borderBottom: "1px solid var(--border)" }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.symbols.map((row) => (
                          <tr key={`${row.symbol_name}-${row.start_line}`} style={{ borderBottom: "1px solid var(--border)" }}>
                            <td style={{ padding: "7px 12px", fontFamily: "ui-monospace, monospace", color: "var(--accent)", fontSize: 12 }}>{row.symbol_name}</td>
                            <td style={{ padding: "7px 12px", color: "var(--text-muted)" }}>{row.chunk_type || "—"}</td>
                            <td style={{ padding: "7px 12px", color: "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>{row.start_line}–{row.end_line}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div>
                <span className="label" style={{ display: "block", marginBottom: 6 }}>Source</span>
                <div style={{ border: "1px solid var(--border)", borderRadius: "var(--r-md)", overflow: "hidden", maxHeight: "42vh", overflowY: "auto" }}>
                  <SyntaxHighlighter language={lang} style={oneLight} showLineNumbers customStyle={SHL_STYLE}>
                    {data.content || ""}
                  </SyntaxHighlighter>
                </div>
              </div>

              <div style={{ paddingTop: 4 }}>
                <button type="button" onClick={handleAsk} className="btn btn-primary" style={{ padding: "9px 20px", fontSize: 13 }}>
                  Ask about this file
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default memo(FileInspectionPanel);
