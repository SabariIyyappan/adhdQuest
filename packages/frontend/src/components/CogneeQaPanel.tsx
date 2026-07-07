/** Doctor Q&A over child memory — GRAPH_COMPLETION with citations (plan §6 Feature 4). */

import { useState } from "react";
import { askCognee } from "../lib/butterbase";

export function CogneeQaPanel({ childId }: { childId: string }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);

  async function ask() {
    setLoading(true);
    try {
      setAnswer(await askCognee(childId, question));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="cognee-qa">
      <input
        value={question}
        placeholder="Has this child improved on division over the last month?"
        onChange={(e) => setQuestion(e.target.value)}
      />
      <button onClick={ask} disabled={loading || !question}>
        {loading ? "Thinking…" : "Ask"}
      </button>
      {answer != null && <pre className="answer">{JSON.stringify(answer, null, 2)}</pre>}
    </div>
  );
}
