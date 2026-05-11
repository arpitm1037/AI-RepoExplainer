import { memo, useCallback, useEffect } from "react";

function ConfirmDialog({
  open,
  title = "Are you sure?",
  description,
  confirmText = "Confirm",
  cancelText = "Cancel",
  danger = false,
  onConfirm,
  onCancel,
}) {
  const cancel = useCallback(() => onCancel?.(), [onCancel]);
  const confirm = useCallback(() => onConfirm?.(), [onConfirm]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape") cancel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, cancel]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 100,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        background: "rgba(0,0,0,0.45)",
        backdropFilter: "blur(8px)",
      }}
      onMouseDown={cancel}
    >
      <div
        className="card"
        style={{
          width: "100%",
          maxWidth: 520,
          padding: 22,
          boxShadow: "var(--shadow-md)",
        }}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 16, fontWeight: 800, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
              {title}
            </div>
            {description && (
              <div style={{ marginTop: 8, fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                {description}
              </div>
            )}
          </div>
          <button type="button" className="btn btn-ghost" onClick={cancel} style={{ padding: "7px 10px" }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div style={{ marginTop: 18, display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button type="button" className="btn btn-secondary" onClick={cancel} style={{ padding: "9px 16px" }}>
            {cancelText}
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={confirm}
            style={{
              padding: "9px 16px",
              background: danger ? "#111111" : "var(--accent)",
            }}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

export default memo(ConfirmDialog);

