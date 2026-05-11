import { memo, useCallback, useState } from "react";

const COLLAPSE_KEY = "codebase-ai-conv-sidebar-collapsed";

const ConvItem = memo(function ConvItem({ conv, isActive, onSelect, onDelete, collapsed }) {
  const click = useCallback(() => onSelect(conv.id), [conv.id, onSelect]);
  const del = useCallback((e) => { e.preventDefault(); e.stopPropagation(); onDelete?.(conv.id); }, [onDelete, conv.id]);

  if (collapsed) {
    return (
      <button
        onClick={click}
        title={conv.title}
        style={{
          width: 32, height: 32,
          borderRadius: 8,
          border: isActive ? "2px solid var(--accent)" : "1px solid var(--border)",
          background: isActive ? "var(--bg-muted)" : "none",
          cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          color: isActive ? "var(--text-primary)" : "var(--text-muted)",
          flexShrink: 0,
        }}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </button>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <button onClick={click} className={`nav-item${isActive ? " active" : ""}`} style={{ flex: 1, minWidth: 0 }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {conv.title}
        </span>
      </button>
      <button
        type="button"
        onClick={del}
        className="btn btn-ghost"
        aria-label="Delete chat"
        title="Delete chat"
        style={{ padding: "5px 7px", borderRadius: 8, flexShrink: 0 }}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="3 6 5 6 21 6"/>
          <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
          <path d="M10 11v6M14 11v6"/>
          <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
        </svg>
      </button>
    </div>
  );
});

function ConversationSidebar({ conversations, activeId, setActiveId, onNew, onDelete }) {
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem(COLLAPSE_KEY) === "true"; } catch { return false; }
  });

  const toggleCollapse = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      try { localStorage.setItem(COLLAPSE_KEY, String(next)); } catch { /* ignore */ }
      return next;
    });
  }, []);

  // ── Collapsed view ──────────────────────────────────────────────────────────
  if (collapsed) {
    return (
      <div style={{
        width: 52,
        background: "var(--bg)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        flexShrink: 0,
        paddingTop: 12,
        gap: 8,
      }}>
        {/* Brand icon */}
        <div style={{
          width: 32, height: 32,
          background: "var(--accent)",
          borderRadius: 8,
          display: "flex", alignItems: "center", justifyContent: "center",
          flexShrink: 0,
          marginBottom: 4,
        }}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="4" y="4" width="7" height="7" rx="2"/>
            <rect x="13" y="4" width="7" height="7" rx="2" opacity="0.85"/>
            <rect x="4" y="13" width="7" height="7" rx="2" opacity="0.85"/>
            <rect x="13" y="13" width="7" height="7" rx="2"/>
          </svg>
        </div>

        {/* Expand button */}
        <button
          onClick={toggleCollapse}
          title="Expand sidebar"
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

        {/* New chat */}
        <button
          onClick={onNew}
          title="New chat"
          style={{
            width: 32, height: 32,
            background: "var(--accent)",
            border: "none",
            borderRadius: 8,
            cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "#fff",
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </button>

        {/* Conversation dots */}
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4, alignItems: "center" }}>
          {conversations.slice(0, 8).map((c) => (
            <ConvItem key={c.id} conv={c} isActive={activeId === c.id} onSelect={setActiveId} onDelete={onDelete} collapsed />
          ))}
        </div>
      </div>
    );
  }

  // ── Expanded view ───────────────────────────────────────────────────────────
  return (
    <div style={{
      width: 260,
      background: "var(--bg)",
      borderRight: "1px solid var(--border)",
      display: "flex",
      flexDirection: "column",
      flexShrink: 0,
    }}>
      {/* Brand + collapse */}
      <div style={{ padding: "18px 16px 14px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
            <div style={{
              width: 32, height: 32,
              background: "var(--accent)",
              borderRadius: 8,
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0,
              boxShadow: "0 2px 6px rgba(0,0,0,0.15)",
            }}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="4" y="4" width="7" height="7" rx="2"/>
                <rect x="13" y="4" width="7" height="7" rx="2" opacity="0.85"/>
                <rect x="4" y="13" width="7" height="7" rx="2" opacity="0.85"/>
                <rect x="13" y="13" width="7" height="7" rx="2"/>
              </svg>
            </div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 800, color: "var(--text-primary)", lineHeight: 1.15, letterSpacing: "-0.01em" }}>Codebase AI</div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.25 }}>Repository Intelligence</div>
            </div>
          </div>
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

        <button onClick={onNew} className="btn btn-primary" style={{ width: "100%", justifyContent: "center", padding: "10px 14px", fontSize: 14 }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New Chat
        </button>
      </div>

      <div style={{ padding: "12px 12px 6px" }}>
        <span className="label" style={{ paddingLeft: 4 }}>History</span>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "4px 10px 14px", display: "flex", flexDirection: "column", gap: 4 }}>
        {conversations.length === 0 ? (
          <p style={{ fontSize: 14, color: "var(--text-muted)", textAlign: "center", padding: "24px 0" }}>No chats yet</p>
        ) : conversations.map((c) => (
          <ConvItem key={c.id} conv={c} isActive={activeId === c.id} onSelect={setActiveId} onDelete={onDelete} collapsed={false} />
        ))}
      </div>
    </div>
  );
}

export default memo(ConversationSidebar);
