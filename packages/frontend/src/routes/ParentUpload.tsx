/** Parent upload flow — select child, upload PDF, wait for the game (plan §7 Person C). */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadAssignmentPdf } from "../lib/butterbase";

export function ParentUpload({ childId }: { childId: string }) {
  const [status, setStatus] = useState<"idle" | "uploading" | "generating">("idle");
  const navigate = useNavigate();

  async function onFile(file: File) {
    setStatus("uploading");
    await uploadAssignmentPdf(childId, file);
    // Pipeline 1 runs server-side; GameFrame subscribes for the game_ready event.
    setStatus("generating");
    navigate(`/play/${childId}`);
  }

  return (
    <section className="parent-upload">
      <h1>Upload today's homework</h1>
      <input
        type="file"
        accept="application/pdf"
        disabled={status !== "idle"}
        onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
      />
      {status === "uploading" && <p>Uploading…</p>}
      {status === "generating" && <p>Generating your game…</p>}
    </section>
  );
}
