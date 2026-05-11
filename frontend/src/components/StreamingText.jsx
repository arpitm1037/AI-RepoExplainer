import { memo } from "react";
import ReactMarkdown from "react-markdown";

function StreamingText({ content }) {
  const text = content == null ? "" : String(content);

  if (!text.trim()) {
    return (
      <p style={{ fontSize: 13, color: "var(--text-muted)", fontStyle: "italic" }}>
        No answer returned. Verify{" "}
        <code style={{ background: "var(--bg-muted)", padding: "1px 5px", borderRadius: 4, fontSize: 12 }}>GROQ_API_KEY</code>
        {" "}on the backend.
      </p>
    );
  }

  return (
    <div className="prose">
      <ReactMarkdown>{text}</ReactMarkdown>
    </div>
  );
}

export default memo(StreamingText);
