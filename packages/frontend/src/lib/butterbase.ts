/**
 * Butterbase SDK client — the single point of contact with the backend.
 * Auth, REST, realtime, and serverless-function calls all flow through here so
 * routes/components never talk to raw fetch endpoints.
 */

import { createClient } from "butterbase";
import type { SessionChannelEvent } from "@adhdquest/contracts";
import { sessionChannel } from "@adhdquest/contracts";

export const bb = createClient({
  url: import.meta.env.VITE_BUTTERBASE_URL,
  anonKey: import.meta.env.VITE_BUTTERBASE_ANON_KEY,
});

/** Subscribe to a child's session channel (Contract C). Returns an unsubscribe fn. */
export function subscribeToSession(
  childId: string,
  onEvent: (event: SessionChannelEvent) => void,
): () => void {
  const channel = bb.realtime.channel(sessionChannel(childId));
  channel.on("message", (msg: SessionChannelEvent) => onEvent(msg));
  channel.subscribe();
  return () => channel.unsubscribe();
}

/** Upload a homework PDF; returns the created assignment id. */
export async function uploadAssignmentPdf(childId: string, file: File): Promise<string> {
  const key = `assignments/${childId}/${crypto.randomUUID()}.pdf`;
  await bb.storage.upload(key, file, { contentType: "application/pdf" });
  const assignment = await bb.rest.insert("assignments", {
    child_id: childId,
    pdf_storage_key: key,
  });
  return assignment.id;
}

/** Doctor Q&A over child memory (calls the cognee-qa serverless function). */
export async function askCognee(childId: string, question: string): Promise<unknown> {
  return bb.functions.invoke("cognee-qa", { child_id: childId, question });
}
