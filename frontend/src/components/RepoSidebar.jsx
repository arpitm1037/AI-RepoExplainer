import { memo, useCallback, useEffect, useRef, useState } from "react";
import { cancelIngestion, getIngestionStatus } from "../api/api";

// Steps shown during ingestion — matches backend on_step labels
const STEPS = [
  "Cloning repository…",
  "Scanning files…",
  "Loading documents…",
  "Building dependency graph…",
  "Chunking code…",
  "Generating embeddings…",
  "Saving index…",
];

const TOTAL = STEPS.length;

// Collapse state persisted to localStorage
const COLLAPSE_KEY = "codebase-ai-repo-sidebar-collapsed";

function RepoSidebar({ repoUrl, setRepoUrl, onIngest, ingesting, currentRepo, chatId }) {
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem(COLLAPSE_KEY) === "true"; } catch { return false; }
  });

  // Live ingestion progress polled from backend
  const [stepLabel, setStepLabel] = useState("");
  const [stepIndex, setStepIndex] = useState(0);
  const [stopping, setStopping] = useState(false);

  const pollRef = useRef(null);

  // Start polling when ingesting begins
  useEffect(() => {
    if (!ingesting || !chatId) {
      clearInterval(pollRef.current);
      return;
    }

    const poll = async () => {
      try {
        const s = await getIngestionStatus(chatId);
        setStepLabel(s.step || "");
        setStepIndex(s.step_index || 0);
      } catch { /* ignore poll errors */ }
    };

    poll();
    pollRef.current = setInterval(poll, 800);
    return () => clearInterval(pollRef.current);
  }, [ingesting, chatId]);

  // Reset step state when ingestion ends
  useEffect(() => {
    if (ingesting) return;
    const t = setTimeout(() => {
      setStepLabel("");
      setStepIndex(0);
      setStopping(false);
    }, 0);
    return () => clearTimeout(t);
  }, [ingesting]);

  const toggleCollapse = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      try { localStorage.setItem(COLLAPSE_KEY, String(next)); } catch { /* ignore */ }
      return next;
    });
  }, []);

  const handleStop = useCallback(async () => {
    if (!chatId || stopping) return;
    setStopping(true);
    try {
      await cancelIngestion(chatId);
    } catch { /* ignore */ }
  }, [chatId, stopping]);

  const progressPct = TOTAL > 0 ? Math.round((stepIndex / TOTAL) * 100) : 0;

  // ── Collapsed view ──────────────────────────────────────────────────────────
  if (collapsed) {
    return (
      <div style={{
        width: 48,
        background: "var(--bg)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        flexShrink: 0,
        paddingTop: 12,
        gap: 8,
      }}>
        <button
          onClick={toggleCollapse}
          title="Expand repository sidebar"
          style={{
            width: 32, height: 32,
            background: "none",
            border: "1px solid var(--border)",
            borderRadius: 8,
            cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "var(--text-muted)",
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </button>

        {/* Repo status dot */}
        <div title={currentRepo || "No repository"} style={{
          width: 8, height: 8, borderRadius: "50%",
          background: currentRepo ? "var(--green)" : "var(--border-strong)",
          marginTop: 4,
        }} />

        {/* Ingesting indicator */}
        {ingesting && (
          <span className="spinner" style={{ marginTop: 4 }} />
        )}
      </div>
    );
  }

  // ── Expanded view ───────────────────────────────────────────────────────────
  return (
    <div style={{
      width: 264,
      background: "var(--bg)",
      borderRight: "1px solid var(--border)",
      display: "flex",
      flexDirection: "column",
      flexShrink: 0,
      transition: "width 0.2s ease",
    }}>

      {/* Header */}
      <div style={{
        padding: "16px 16px 14px",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <span className="label">Repository</span>
        <button
          onClick={toggleCollapse}
          title="Collapse sidebar"
          style={{
            background: "none", border: "none", cursor: "pointer",
            color: "var(--text-muted)", padding: 4, borderRadius: 6,
            display: "flex", alignItems: "center",
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
      </div>

      {/* URL input + ingest button */}
      <div style={{ padding: "14px 16px 14px", borderBottom: "1px solid var(--border)" }}>
        <input
          type="text"
          placeholder="https://github.com/owner/repo"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          disabled={ingesting}
          className="input"
          style={{ marginBottom: 10, fontSize: 13 }}
        />

        {ingesting ? (
          /* ── Active ingestion UI ── */
          <div>
            {/* Progress bar */}
            <div style={{
              height: 4,
              background: "var(--bg-muted)",
              borderRadius: 99,
              overflow: "hidden",
              marginBottom: 10,
            }}>
              <div style={{
                height: "100%",
                width: `${progressPct}%`,
                background: "var(--accent)",
                borderRadius: 99,
                transition: "width 0.4s ease",
              }} />
            </div>

            {/* Current step */}
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginBottom: 10,
            }}>
              <span className="spinner spinner-sm" style={{ flexShrink: 0 }} />
              <span style={{
                fontSize: 13,
                color: "var(--text-secondary)",
                fontWeight: 500,
                flex: 1,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}>
                {stepLabel || "Starting…"}
              </span>
              <span style={{ fontSize: 11, color: "var(--text-muted)", flexShrink: 0 }}>
                {stepIndex}/{TOTAL}
              </span>
            </div>

            {/* Step list */}
            <div style={{ display: "flex", flexDirection: "column", gap: 3, marginBottom: 12 }}>
              {STEPS.map((s, i) => {
                const done = i + 1 < stepIndex;
                const active = i + 1 === stepIndex;
                return (
                  <div key={s} style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 7,
                    opacity: done || active ? 1 : 0.35,
                  }}>
                    <div style={{
                      width: 16, height: 16,
                      borderRadius: "50%",
                      flexShrink: 0,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      background: done ? "var(--green)" : active ? "var(--accent)" : "var(--bg-muted)",
                      border: `1px solid ${done ? "var(--green-border)" : active ? "var(--border-strong)" : "var(--border)"}`,
                      transition: "background 0.2s",
                    }}>
                      {done ? (
                        <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                      ) : active ? (
                        <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#fff", display: "block" }} />
                      ) : null}
                    </div>
                    <span style={{
                      fontSize: 12,
                      color: active ? "var(--text-primary)" : done ? "var(--green)" : "var(--text-muted)",
                      fontWeight: active ? 600 : 400,
                    }}>
                      {s}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Stop button */}
            <button
              onClick={handleStop}
              disabled={stopping}
              className="btn btn-secondary"
              style={{ width: "100%", justifyContent: "center", fontSize: 13, padding: "8px 14px", borderColor: "#fca5a5", color: stopping ? "var(--text-muted)" : "var(--red)" }}
            >
              {stopping ? (
                <><span className="spinner spinner-sm" /> Stopping…</>
              ) : (
                <>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                  </svg>
                  Stop Ingestion
                </>
              )}
            </button>
          </div>
        ) : (
          /* ── Idle ingest button ── */
          <button
            onClick={onIngest}
            disabled={!repoUrl.trim()}
            className="btn btn-primary"
            style={{ width: "100%", justifyContent: "center", padding: "10px 14px", fontSize: 14 }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            Ingest Repository
          </button>
        )}
      </div>

      {/* Status / tips */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px" }}>
        {currentRepo ? (
          <>
            <div style={{
              background: "var(--green-light)",
              border: "1px solid var(--green-border)",
              borderRadius: "var(--r-md)",
              padding: "12px 14px",
              marginBottom: 18,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 5 }}>
                <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--green)", display: "inline-block", flexShrink: 0 }} />
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--green)" }}>Indexed & Ready</span>
              </div>
              <p style={{ fontSize: 12, color: "#166534", wordBreak: "break-all", lineHeight: 1.5 }}>
                {currentRepo}
              </p>
            </div>

            <span className="label" style={{ display: "block", marginBottom: 8 }}>Suggested Prompts</span>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              {[
                "What are the main modules?",
                "Show me the entry points",
                "Explain the architecture",
                "List all API routes",
              ].map((p) => (
                <div key={p} style={{
                  fontSize: 13,
                  color: "var(--text-secondary)",
                  padding: "9px 12px",
                  borderRadius: "var(--r)",
                  border: "1px solid var(--border)",
                  background: "var(--bg-subtle)",
                  lineHeight: 1.4,
                  cursor: "default",
                }}>
                  {p}
                </div>
              ))}
            </div>
          </>
        ) : !ingesting ? (
          <div style={{ textAlign: "center", paddingTop: 32 }}>
            <div style={{
              width: 44, height: 44,
              background: "var(--bg-muted)",
              border: "1px solid var(--border)",
              borderRadius: "var(--r-md)",
              display: "flex", alignItems: "center", justifyContent: "center",
              margin: "0 auto 14px",
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 3h6l2 3h10a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/>
              </svg>
            </div>
            <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.6 }}>
              Paste a GitHub URL above<br />and click Ingest to begin
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default memo(RepoSidebar);
