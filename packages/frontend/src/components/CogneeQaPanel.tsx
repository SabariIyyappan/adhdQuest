import { useState } from "react";
import { askCognee } from "../lib/butterbase";
import { Send, Bot, User, Bookmark } from "lucide-react";
import { LoadingSkeleton } from "./ui/LoadingSkeleton";

interface Citation {
  level_index?: number;
  event_type?: string;
  details?: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "bot";
  text: string;
  citations?: Citation[];
}

export function CogneeQaPanel({ childId }: { childId: string }) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "initial",
      role: "bot",
      text: "Hello, I am the Cognee memory analysis agent. Ask me anything about this child's cognitive learning sessions, struggles, or topic progression trends.",
    },
  ]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await askCognee(childId, userMessage.text);
      const botMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "bot",
        text: response.answer || "I processed the history graph but couldn't synthesize a narrative.",
        citations: response.citations || [],
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      const botMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "bot",
        text: "Error calling clinical memory assistant.",
      };
      setMessages((prev) => [...prev, botMessage]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "380px", backgroundColor: "var(--color-bg)", borderRadius: "12px", border: "1px solid var(--color-border)", overflow: "hidden" }}>
      {/* Messages Stream */}
      <div style={{ flex: 1, padding: "1rem", overflowY: "auto", display: "flex", flexDirection: "column", gap: "1rem" }}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: "flex",
              gap: "0.75rem",
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "85%",
            }}
          >
            {msg.role === "bot" && (
              <div style={{
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                backgroundColor: "rgba(253, 203, 110, 0.1)",
                color: "var(--color-accent)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0
              }}>
                <Bot size={16} />
              </div>
            )}
            
            <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              <div
                style={{
                  padding: "0.75rem 1rem",
                  borderRadius: "16px",
                  backgroundColor: msg.role === "user" ? "var(--color-primary)" : "var(--color-surface)",
                  color: "#fff",
                  fontSize: "0.9rem",
                  fontWeight: "600",
                  border: msg.role === "bot" ? "1px solid var(--color-border)" : "none",
                  borderTopRightRadius: msg.role === "user" ? "4px" : "16px",
                  borderTopLeftRadius: msg.role === "bot" ? "4px" : "16px",
                  lineHeight: 1.4
                }}
              >
                {msg.text}
              </div>

              {/* Citations Pill list */}
              {msg.citations && msg.citations.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginTop: "0.25rem" }}>
                  {msg.citations.map((c, index) => (
                    <span
                      key={index}
                      className="role-badge doctor"
                      style={{
                        fontSize: "0.7rem",
                        padding: "0.1rem 0.5rem",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.25rem",
                        cursor: "help"
                      }}
                      title={c.details}
                    >
                      <Bookmark size={10} />
                      Level {c.level_index || "N/A"}: {c.event_type || "memory"}
                    </span>
                  ))}
                </div>
              )}
            </div>
            
            {msg.role === "user" && (
              <div style={{
                width: "32px",
                height: "32px",
                borderRadius: "50%",
                backgroundColor: "rgba(108, 92, 231, 0.15)",
                color: "var(--color-primary)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0
              }}>
                <User size={16} />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div style={{ display: "flex", gap: "0.75rem", alignSelf: "flex-start", width: "70%" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "50%", backgroundColor: "var(--color-border)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Bot size={16} />
            </div>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.25rem" }}>
              <LoadingSkeleton height={36} />
            </div>
          </div>
        )}
      </div>

      {/* Input bar */}
      <form onSubmit={handleSend} style={{ display: "flex", padding: "0.75rem", backgroundColor: "var(--color-surface)", borderTop: "1px solid var(--color-border)", gap: "0.5rem" }}>
        <input
          type="text"
          className="form-input"
          style={{ flex: 1, padding: "0.5rem 1rem", backgroundColor: "var(--color-bg)" }}
          placeholder="Ask something about the memory graphs..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className="btn btn-primary"
          style={{ padding: "0.5rem 1rem", display: "flex", alignItems: "center", justifyContent: "center" }}
          disabled={loading || !input.trim()}
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
