import { memo, useCallback, useEffect, useMemo, useState } from "react";
import { getExplorationData } from "../api/api";

function segs(p) { return String(p).split(/[/\\]/).filter(Boolean); }

function buildTree(files) {
  const root = { segment: "", children: {}, files: [] };
  for (const f of files) {
    const parts = segs(f.file_path);
    if (!parts.length) continue;
    let node = root;
    for (let i = 0; i < parts.length - 1; i++) {
      const s = parts[i];
      if (!node.children[s]) node.children[s] = { segment: s, children: {}, files: [] };
      node = node.children[s];
    }
    node.files.push({ ...f, fileName: parts[parts.length - 1] });
  }
  return root;
}

function collectKeys(folder, prefix) {
  const keys = [];
  for (const name of Object.keys(folder.children)) {
    const k = [prefix, name].filter(Boolean).join("/");
    keys.push(k, ...collectKeys(folder.children[name], k));
  }
  return keys;
}

// ── FileRow ──────────────────────────────────────────────────────────────────
const FileRow = memo(function FileRow({ file, isSelected, depth, onSelect, onAsk, onInspect }) {
  const rowId = `ef-${encodeURIComponent(file.file_path).replace(/%/g, "_")}`;
  const doSelect  = useCallback(() => onSelect(file.file_path),  [onSelect,  file.file_path]);
  const doInspect = useCallback(() => onInspect(file.file_path), [onInspect, file.file_path]);
  const doAsk     = useCallback(() => onAsk(file.file_path),     [onAsk,     file.file_path]);

  const ext = file.fileName.includes(".") ? file.fileName.slice(file.fileName.lastIndexOf(".")) : "";

  return (
    <div
      id={rowId}
      style={{
        marginLeft: depth * 16,
        marginBottom: 3,
        borderRadius: "var(--r-md)",
        border: `1px solid ${isSelected ? "var(--border-strong)" : "var(--border)"}`,
        background: isSelected ? "var(--bg-muted)" : "var(--bg)",
        overflow: "hidden",
        transition: "border-color 0.12s, background 0.12s",
        boxShadow: isSelected ? "0 0 0 2px rgba(17,17,17,0.08)" : "var(--shadow-sm)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, padding: "9px 12px" }}>
        <button type="button" onClick={doSelect} style={{ flex: 1, minWidth: 0, textAlign: "left", background: "none", border: "none", cursor: "pointer", padding: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
            {ext && (
              <span style={{
                fontSize: 10, fontWeight: 600,
                color: isSelected ? "var(--text-primary)" : "var(--text-muted)",
                fontFamily: "ui-monospace, monospace",
                background: isSelected ? "var(--border)" : "var(--bg-muted)",
                padding: "1px 5px", borderRadius: 4, flexShrink: 0,
              }}>{ext}</span>
            )}
            <span style={{ fontSize: 14, fontWeight: 600, color: isSelected ? "var(--text-primary)" : "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {file.fileName}
            </span>
          </div>
          {!isSelected && file.summary && (
            <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 1, WebkitBoxOrient: "vertical" }}>
              {file.summary}
            </p>
          )}
        </button>

        <div style={{ display: "flex", alignItems: "center", gap: 5, flexShrink: 0 }}>
          <span className="badge badge-gray" style={{ fontSize: 11 }}>{file.dependency_count}d</span>
          <span className="badge badge-gray" style={{ fontSize: 11 }}>{file.symbol_count}s</span>
          <button type="button" onClick={doInspect} className="btn btn-ghost" style={{ padding: "3px 8px", fontSize: 11 }}>
            Inspect
          </button>
        </div>
      </div>

      {isSelected && (
        <div style={{ borderTop: "1px solid var(--accent-border)", padding: "12px 12px 12px", background: "var(--bg)" }}>
          {file.summary && (
            <div style={{ marginBottom: 12 }}>
              <span className="label" style={{ display: "block", marginBottom: 5 }}>Summary</span>
              <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.65, whiteSpace: "pre-wrap", background: "var(--bg-subtle)", border: "1px solid var(--border)", borderRadius: "var(--r)", padding: "10px 12px", maxHeight: 130, overflowY: "auto" }}>
                {file.summary}
              </p>
            </div>
          )}

          {Array.isArray(file.symbols_preview) && file.symbols_preview.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <span className="label" style={{ display: "block", marginBottom: 5 }}>
                Symbols
                {file.symbol_count > file.symbols_preview.length && (
                  <span style={{ fontWeight: 400, textTransform: "none", letterSpacing: 0, color: "var(--text-muted)", marginLeft: 4 }}>
                    ({file.symbols_preview.length} shown)
                  </span>
                )}
              </span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {file.symbols_preview.map((s) => <span key={s} className="tag">{s}</span>)}
              </div>
            </div>
          )}

          {file.dependencies?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <span className="label" style={{ display: "block", marginBottom: 5 }}>Imports</span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4, maxHeight: 72, overflowY: "auto" }}>
                {file.dependencies.map((d, i) => <span key={`${d}-${i}`} className="tag" style={{ color: "var(--text-muted)" }}>{d}</span>)}
              </div>
            </div>
          )}

          <div style={{ display: "flex", gap: 8 }}>
            <button type="button" onClick={doAsk} className="btn btn-primary" style={{ padding: "6px 14px", fontSize: 12 }}>
              Ask about this file
            </button>
            <button type="button" onClick={doInspect} className="btn btn-secondary" style={{ padding: "6px 12px", fontSize: 12 }}>
              Open inspection
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

// ── TreeFolder ────────────────────────────────────────────────────────────────
const TreeFolder = memo(function TreeFolder({ folder, depth, expanded, toggle, selectedPath, onSelect, onAsk, onInspect }) {
  const names = useMemo(() => Object.keys(folder.children).sort((a, b) => a.localeCompare(b)), [folder.children]);
  const files = useMemo(() => [...folder.files].sort((a, b) => a.fileName.localeCompare(b.fileName)), [folder.files]);

  return (
    <div>
      {names.map((name) => {
        const child = folder.children[name];
        const key   = [folder.segment, name].filter(Boolean).join("/");
        const open  = expanded.has(key);
        return (
          <div key={key} style={{ marginLeft: depth * 16 }}>
            <button
              type="button"
              onClick={() => toggle(key)}
              style={{
                width: "100%", display: "flex", alignItems: "center", gap: 7,
                padding: "6px 8px", background: "none", border: "none", cursor: "pointer",
                borderRadius: "var(--r)", color: "var(--text-secondary)", fontSize: 13, fontWeight: 500,
                fontFamily: "inherit",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = "var(--bg-hover)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = "none"; }}
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
                style={{ flexShrink: 0, transition: "transform 0.12s", transform: open ? "rotate(90deg)" : "none" }}>
                <polyline points="9 18 15 12 9 6"/>
              </svg>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                style={{ flexShrink: 0, color: "var(--text-muted)" }}>
                <path d="M3 3h6l2 3h10a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/>
              </svg>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{name}</span>
            </button>
            {open && (
              <TreeFolder folder={child} depth={depth + 1} expanded={expanded} toggle={toggle}
                selectedPath={selectedPath} onSelect={onSelect} onAsk={onAsk} onInspect={onInspect} />
            )}
          </div>
        );
      })}
      {files.map((f) => (
        <FileRow key={f.file_path} file={f} depth={depth}
          isSelected={selectedPath === f.file_path}
          onSelect={onSelect} onAsk={onAsk} onInspect={onInspect} />
      ))}
    </div>
  );
});

// ── RepositoryExplorer ────────────────────────────────────────────────────────
function RepositoryExplorer({ chatId, currentRepo, selectedPath, onSelectFile, onAskAboutFile, onInspectFile }) {
  const [files,    setFiles]    = useState([]);
  const [search,   setSearch]   = useState("");
  const [loading,  setLoading]  = useState(false);
  const [expanded, setExpanded] = useState(() => new Set());

  useEffect(() => {
    if (!currentRepo || !chatId) return;
    let dead = false;
    (async () => {
      try {
        setLoading(true);
        const d = await getExplorationData(chatId);
        if (!dead) setFiles(d.files || []);
      } catch (e) { console.error(e); }
      finally { if (!dead) setLoading(false); }
    })();
    return () => { dead = true; };
  }, [currentRepo, chatId]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return files;
    return files.filter((f) =>
      f.file_path.toLowerCase().includes(q) ||
      (f.summary && String(f.summary).toLowerCase().includes(q)) ||
      (Array.isArray(f.symbols_preview) && f.symbols_preview.some((s) => s.toLowerCase().includes(q)))
    );
  }, [files, search]);

  const tree = useMemo(() => buildTree(filtered), [filtered]);

  const autoExpanded = useMemo(() => {
    if (!search.trim()) return new Set();
    return new Set(collectKeys(tree, ""));
  }, [search, tree]);

  const effectiveExpanded = useMemo(() => {
    const m = new Set(expanded);
    autoExpanded.forEach((k) => m.add(k));
    return m;
  }, [expanded, autoExpanded]);

  const toggle = useCallback((key) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }, []);

  useEffect(() => {
    if (!selectedPath) return;
    const id = `ef-${encodeURIComponent(selectedPath).replace(/%/g, "_")}`;
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [selectedPath]);

  if (!currentRepo) return null;

  return (
    <div className="card" style={{ overflow: "hidden" }}>
      {/* Header */}
      <div style={{ padding: "18px 24px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h3 style={{ fontSize: 17, fontWeight: 700, color: "var(--text-primary)", marginBottom: 3, letterSpacing: "-0.01em" }}>Repository Explorer</h3>
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
            {files.length} files indexed · click a file to explore
          </p>
        </div>
        {selectedPath && (
          <span className="badge badge-gray" style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {selectedPath.split(/[/\\]/).pop()}
          </span>
        )}
      </div>

      {/* Search */}
      <div style={{ padding: "12px 24px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ position: "relative" }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }}>
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            type="text"
            placeholder="Search files, symbols, summaries…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input"
            style={{ paddingLeft: 32, fontSize: 13 }}
          />
        </div>
      </div>

      {/* Tree */}
      <div style={{ maxHeight: 580, overflowY: "auto", padding: "10px 16px 16px" }}>
        {loading ? (
          <div style={{ padding: "40px 0", textAlign: "center" }}>
            <span className="spinner" style={{ margin: "0 auto 12px", display: "block" }} />
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading repository structure…</p>
          </div>
        ) : filtered.length === 0 ? (
          <p style={{ fontSize: 13, color: "var(--text-muted)", textAlign: "center", padding: "40px 0" }}>
            {search ? "No files match your search." : "No files indexed yet."}
          </p>
        ) : (
          <TreeFolder
            folder={tree} depth={0} expanded={effectiveExpanded} toggle={toggle}
            selectedPath={selectedPath} onSelect={onSelectFile} onAsk={onAskAboutFile} onInspect={onInspectFile}
          />
        )}
      </div>
    </div>
  );
}

export default memo(RepositoryExplorer);
