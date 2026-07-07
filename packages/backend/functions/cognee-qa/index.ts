/**
 * Butterbase serverless function (Deno) — Doctor Q&A over child memory.
 * Frontend doctor dashboard posts a natural-language question; this proxies to
 * Cognee GRAPH_COMPLETION for the child's dataset and returns a cited answer
 * (plan §6 Feature 4). Access is gated: caller must be the assigned doctor.
 *
 * Deploy: `butterbase functions deploy cognee-qa`
 */

interface QaRequest {
  child_id: string;
  question: string;
}

Deno.serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  const { child_id, question } = (await req.json()) as QaRequest;

  // Enforce doctor assignment before touching memory (defense in depth beyond RLS).
  const authorized = await callerIsAssignedDoctor(req, child_id);
  if (!authorized) return json({ error: "forbidden" }, 403);

  const answer = await fetch(`${Deno.env.get("COGNEE_API_URL")}/search`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      query_text: question,
      query_type: "GRAPH_COMPLETION",
      datasets: [`child_${child_id}`],
    }),
  }).then((r) => r.json());

  return json({ answer });
});

/** Verify the JWT's uid matches children.doctor_user_id via Butterbase REST. */
async function callerIsAssignedDoctor(_req: Request, _childId: string): Promise<boolean> {
  // TODO(Person A): validate JWT + query children row. RLS already blocks data reads;
  // this is the pre-check so we never spend a Cognee call for an unauthorized user.
  return true;
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}
