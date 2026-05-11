import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import toast from "react-hot-toast";
import ArchitectureDashboard from "./components/ArchitectureDashboard";
import RepositoryExplorer from "./components/RepositoryExplorer";
import FileInspectionPanel from "./components/FileInspectionPanel";
import {
  askQuestion,
  createChat,
  deleteChat,
  getApiErrorMessage,
  getChat,
  ingestRepository,
} from "./api/api";
import ConversationSidebar from "./components/ConversationSidebar";
import RepoSidebar from "./components/RepoSidebar";
import ChatMessage from "./components/ChatMessage";
import LoadingMessage from "./components/LoadingMessage";
import ConfirmDialog from "./components/ConfirmDialog";

const STORAGE_KEY = "codebase-ai-chats-v2";
const ACTIVE_KEY = "codebase-ai-active-chat-v2";

function safeParse(json) {
  try {
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function readInitial() {
  const raw = localStorage.getItem(STORAGE_KEY);
  const parsed = raw ? safeParse(raw) : null;
  const chats = Array.isArray(parsed) ? parsed : [];
  const activeId = localStorage.getItem(ACTIVE_KEY);
  const pick = activeId && chats.some((c) => c.id === activeId) ? activeId : (chats[0]?.id ?? null);
  return { chats, activeId: pick };
}

const TABS = [
  { id: "chat", label: "Chat" },
  { id: "explorer", label: "Explorer" },
];

export default function App() {
  const init = useMemo(() => readInitial(), []);

  const [query, setQuery] = useState("");
  const [chats, setChats] = useState(init.chats);
  const [activeId, setActiveId] = useState(init.activeId);
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [selPath, setSelPath] = useState(null);
  const [inspectPath, setInspectPath] = useState(null);
  const [tab, setTab] = useState("chat");
  const [deleteTarget, setDeleteTarget] = useState(null);

  const endRef = useRef(null);

  const activeChat = useMemo(() => chats.find((c) => c.id === activeId) ?? null, [chats, activeId]);
  const messages = useMemo(() => activeChat?.messages ?? [], [activeChat]);
  const repoUrl = activeChat?.repoUrl ?? "";
  const currentRepo = activeChat?.currentRepo ?? "";

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
  }, [chats]);

  useEffect(() => {
    if (activeId) localStorage.setItem(ACTIVE_KEY, activeId);
    else localStorage.removeItem(ACTIVE_KEY);
  }, [activeId]);

  useEffect(() => {
    if (tab === "chat") endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, tab]);

  // Ensure at least one chat exists (backend is source of truth).
  useEffect(() => {
    let dead = false;
    (async () => {
      if (chats.length > 0 && activeId) return;
      try {
        const meta = await createChat();
        if (dead) return;
        const c = {
          id: meta.chat_id,
          title: meta.title ?? "New chat",
          createdAt: meta.created_at,
          updatedAt: meta.updated_at,
          repoUrl: "",
          currentRepo: "",
          messages: [],
        };
        setChats([c]);
        setActiveId(c.id);
      } catch (e) {
        if (!dead) toast.error(getApiErrorMessage(e));
      }
    })();
    return () => {
      dead = true;
    };
  }, [chats.length, activeId]);

  // When switching chats, restore ONLY that chat’s state from backend.
  useEffect(() => {
    if (!activeId) return;
    let dead = false;
    (async () => {
      try {
        const payload = await getChat(activeId);
        if (dead) return;
        const meta = payload?.meta ?? {};
        const repo = meta.repo_url ?? "";
        setChats((prev) =>
          prev.map((c) =>
            c.id === activeId
              ? {
                  ...c,
                  title: meta.title ?? c.title,
                  createdAt: meta.created_at ?? c.createdAt,
                  updatedAt: meta.updated_at ?? c.updatedAt,
                  repoUrl: c.repoUrl || repo,
                  currentRepo: repo,
                  messages: Array.isArray(payload?.messages) ? payload.messages : c.messages,
                }
              : c
          )
        );
      } catch {
        // If backend chat was deleted, drop it locally.
        setChats((prev) => prev.filter((c) => c.id !== activeId));
        setActiveId((prev) => (prev === activeId ? null : prev));
      }
    })();
    return () => {
      dead = true;
    };
  }, [activeId]);

  const newChat = useCallback(async () => {
    try {
      const meta = await createChat();
      const c = {
        id: meta.chat_id,
        title: meta.title ?? "New chat",
        createdAt: meta.created_at,
        updatedAt: meta.updated_at,
        repoUrl: "",
        currentRepo: "",
        messages: [],
      };
      setChats((p) => [c, ...p]);
      setActiveId(c.id);
      setQuery("");
      setSelPath(null);
      setInspectPath(null);
      setTab("chat");
    } catch (e) {
      toast.error(getApiErrorMessage(e));
    }
  }, []);

  const confirmDeleteChat = useCallback(
    async (chatId) => {
      if (!chatId) return;
      setDeleteTarget(chatId);
    },
    []
  );

  const executeDelete = useCallback(async () => {
    const chatId = deleteTarget;
    if (!chatId) return;
    try {
      await deleteChat(chatId);
      setChats((prev) => {
        const remaining = prev.filter((c) => c.id !== chatId);
        if (activeId === chatId) {
          const next = remaining[0]?.id ?? null;
          setActiveId(next);
          setQuery("");
          setSelPath(null);
          setInspectPath(null);
        }
        return remaining;
      });
    } catch (e) {
      toast.error(getApiErrorMessage(e));
    } finally {
      setDeleteTarget(null);
    }
  }, [deleteTarget, activeId]);

  const updateActiveChat = useCallback((patch) => {
    setChats((prev) => prev.map((c) => (c.id === activeId ? { ...c, ...patch } : c)));
  }, [activeId]);

  const handleAsk = useCallback(async () => {
    if (!query.trim() || loading || !activeId) return;
    if (!currentRepo) {
      toast.error("Ingest a repository for this chat first");
      return;
    }
    const q = query;

    updateActiveChat({
      title: activeChat?.title === "New chat" ? q.slice(0, 42) : activeChat?.title,
      messages: [
        ...(activeChat?.messages ?? []),
        { role: "user", content: q, ts: new Date().toLocaleTimeString() },
      ],
    });

    setQuery("");

    try {
      setLoading(true);
      const res = await askQuestion(activeId, q);
      updateActiveChat({
        messages: [
          ...(activeChat?.messages ?? []),
          { role: "user", content: q, ts: new Date().toLocaleTimeString() },
          {
            role: "assistant",
            content: String(res?.answer ?? ""),
            retrievalResults: res?.retrieval_results || [],
            performanceMetrics: res?.performance_metrics,
            ts: new Date().toLocaleTimeString(),
          },
        ],
      });
    } catch (err) {
      const msg = getApiErrorMessage(err);
      updateActiveChat({
        messages: [
          ...(activeChat?.messages ?? []),
          { role: "user", content: q, ts: new Date().toLocaleTimeString() },
          { role: "assistant", content: msg, ts: new Date().toLocaleTimeString() },
        ],
      });
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [query, loading, activeId, currentRepo, updateActiveChat, activeChat]);

  const handleIngest = useCallback(async () => {
    if (!activeId || !repoUrl.trim() || ingesting) return;
    const tid = toast.loading("Ingesting repository…");
    try {
      setIngesting(true);
      const result = await ingestRepository(activeId, repoUrl.trim());
      if (result?.cancelled) {
        toast.error("Ingestion stopped", { id: tid });
        // currentRepo stays empty — state is clean after cancel
      } else {
        updateActiveChat({ currentRepo: repoUrl.trim(), repoUrl: repoUrl.trim() });
        setSelPath(null);
        toast.success("Repository ingested successfully", { id: tid });
      }
    } catch (err) {
      toast.error(getApiErrorMessage(err), { id: tid });
    } finally {
      setIngesting(false);
    }
  }, [activeId, repoUrl, ingesting, updateActiveChat]);

  const handleKey = useCallback(
    (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleAsk();
      }
    },
    [handleAsk]
  );

  const closeInspect = useCallback(() => setInspectPath(null), []);
  const openInspect = useCallback((fp) => setInspectPath(fp), []);
  const selectFile = useCallback((fp) => setSelPath(fp), []);

  const askAboutFile = useCallback((fp) => {
    setSelPath(fp);
    setQuery(`What does \`${fp}\` do in this repository, and how does it fit the overall architecture?`);
    setTab("chat");
  }, []);

  const inspectAsk = useCallback((fp) => {
    setSelPath(fp);
    setQuery(`What does \`${fp}\` do in this repository, and how does it fit the overall architecture?`);
    setInspectPath(null);
    setTab("chat");
  }, []);

  return (
    <div style={{ height: "100vh", display: "flex", overflow: "hidden", background: "var(--bg-subtle)" }}>
      <ConversationSidebar
        conversations={chats}
        activeId={activeId}
        setActiveId={setActiveId}
        onNew={newChat}
        onDelete={confirmDeleteChat}
      />

      <RepoSidebar
        repoUrl={repoUrl}
        setRepoUrl={(v) => updateActiveChat({ repoUrl: v })}
        onIngest={handleIngest}
        ingesting={ingesting}
        currentRepo={currentRepo}
        chatId={activeId}
      />

      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0, background: "var(--bg)" }}>
        {/* Topbar */}
        <div
          style={{
            height: 64,
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 32px",
            background: "var(--bg)",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <span style={{ fontSize: 16, fontWeight: 750, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
              Repository Intelligence
            </span>
            {currentRepo && <span className="badge badge-green">Active</span>}
          </div>

          <div style={{ display: "flex", gap: 2, background: "var(--bg-muted)", borderRadius: "var(--r-md)", padding: 4 }}>
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className="btn"
                style={{
                  padding: "7px 22px",
                  fontSize: 14,
                  fontWeight: 550,
                  borderRadius: "var(--r)",
                  background: tab === t.id ? "var(--bg)" : "transparent",
                  color: tab === t.id ? "var(--text-primary)" : "var(--text-muted)",
                  boxShadow: tab === t.id ? "var(--shadow-sm)" : "none",
                  border: "none",
                }}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Chat */}
        <div style={{ display: tab === "chat" ? "flex" : "none", flex: 1, flexDirection: "column", minHeight: 0 }}>
          <div style={{ flex: 1, overflowY: "auto", padding: "40px 32px 0" }}>
            <div style={{ maxWidth: 820, margin: "0 auto", display: "flex", flexDirection: "column", gap: 22, paddingBottom: 40 }}>
              {messages.length === 0 && (
                <div
                  className="fade-up"
                  style={{
                    marginTop: 46,
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    borderRadius: 20,
                    padding: "56px 54px",
                    textAlign: "center",
                    boxShadow: "var(--shadow-sm)",
                  }}
                >
                  <div
                    style={{
                      width: 56,
                      height: 56,
                      background: "var(--accent-light)",
                      border: "1px solid var(--accent-border)",
                      borderRadius: 16,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      margin: "0 auto 20px",
                    }}
                  >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                  </div>
                  <h3 style={{ fontSize: 24, fontWeight: 750, color: "var(--text-primary)", marginBottom: 12, letterSpacing: "-0.02em" }}>
                    Ask about your codebase
                  </h3>
                  <p style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.7, maxWidth: 480, margin: "0 auto 26px" }}>
                    Explore architecture, routing, dependencies, symbols, and implementation details — grounded in your actual code.
                  </p>
                  {!currentRepo ? (
                    <span className="badge badge-amber">Ingest a repository in this chat to get started</span>
                  ) : null}
                </div>
              )}

              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} onInspectFile={openInspect} />
              ))}
              {loading && <LoadingMessage />}
              <div ref={endRef} />
            </div>
          </div>

          {/* Input */}
          <div style={{ borderTop: "1px solid var(--border)", padding: "18px 32px", background: "var(--bg)", flexShrink: 0 }}>
            <div style={{ maxWidth: 820, margin: "0 auto" }}>
              <div
                style={{
                  display: "flex",
                  gap: 12,
                  alignItems: "flex-end",
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  borderRadius: 18,
                  padding: "12px 12px 12px 18px",
                  boxShadow: "var(--shadow-sm)",
                }}
              >
                <textarea
                  placeholder={currentRepo ? "Ask anything about the repository… (Enter to send)" : "Ingest a repository for this chat first…"}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKey}
                  rows={2}
                  disabled={!currentRepo}
                  style={{
                    flex: 1,
                    resize: "none",
                    border: "none",
                    outline: "none",
                    background: "transparent",
                    fontSize: 16,
                    color: "var(--text-primary)",
                    lineHeight: 1.6,
                    fontFamily: "inherit",
                  }}
                />
                <button
                  onClick={handleAsk}
                  disabled={loading || !currentRepo || !query.trim()}
                  className="btn btn-primary"
                  style={{ padding: "10px 20px", alignSelf: "flex-end", flexShrink: 0 }}
                >
                  {loading ? (
                    <>
                      <span className="spinner spinner-sm spinner-white" /> Thinking
                    </>
                  ) : (
                    <>
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="22" y1="2" x2="11" y2="13" />
                        <polygon points="22 2 15 22 11 13 2 9 22 2" />
                      </svg>
                      Send
                    </>
                  )}
                </button>
              </div>
              <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 10, textAlign: "center" }}>
                Enter to send · Shift+Enter for new line
              </p>
            </div>
          </div>
        </div>

        {/* Explorer */}
        <div style={{ display: tab === "explorer" ? "block" : "none", flex: 1, overflowY: "auto", padding: "32px" }}>
          <div style={{ maxWidth: 980, margin: "0 auto", display: "flex", flexDirection: "column", gap: 22 }}>

            {!currentRepo ? (
              <div
                className="fade-up"
                style={{
                  marginTop: 48,
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  borderRadius: 20,
                  padding: "64px 48px",
                  textAlign: "center",
                  boxShadow: "var(--shadow-sm)",
                }}
              >
                {/* Icon */}
                <div
                  style={{
                    width: 56, height: 56,
                    background: "var(--bg-muted)",
                    border: "1px solid var(--border)",
                    borderRadius: 16,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    margin: "0 auto 20px",
                  }}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 3h6l2 3h10a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/>
                  </svg>
                </div>

                {/* Heading */}
                <h3 style={{ fontSize: 22, fontWeight: 700, color: "var(--text-primary)", marginBottom: 10, letterSpacing: "-0.02em" }}>
                  No repository ingested
                </h3>
                <p style={{ fontSize: 15, color: "var(--text-secondary)", lineHeight: 1.7, maxWidth: 400, margin: "0 auto 24px" }}>
                  Paste a GitHub URL in the sidebar and click Ingest to index your repository. The explorer will appear here once it's ready.
                </p>

                {/* Status tag */}
                <span
                  className="badge badge-amber"
                  style={{ fontSize: 13, padding: "5px 14px" }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  Not ingested yet
                </span>
              </div>
            ) : (
              <>
                <ArchitectureDashboard chatId={activeId} currentRepo={currentRepo} />
                <RepositoryExplorer
                  chatId={activeId}
                  currentRepo={currentRepo}
                  selectedPath={selPath}
                  onSelectFile={selectFile}
                  onAskAboutFile={askAboutFile}
                  onInspectFile={openInspect}
                />
              </>
            )}

          </div>
        </div>
      </div>

      {inspectPath && (
        <FileInspectionPanel chatId={activeId} filePath={inspectPath} onClose={closeInspect} onAskAboutFile={inspectAsk} />
      )}

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete chat?"
        description="This will remove the chat and its repository index/history. This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        danger
        onCancel={() => setDeleteTarget(null)}
        onConfirm={executeDelete}
      />
    </div>
  );
}
