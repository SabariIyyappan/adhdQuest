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

/**
 * Verify the caller's JWT resolves to a user who is the assigned doctor for this
 * child. RLS already blocks the underlying data reads; this pre-check ensures we
 * never spend a Cognee call (or leak existence) for an unauthorized caller.
 */
async function callerIsAssignedDoctor(req: Request, childId: string): Promise<boolean> {
  const authHeader = req.headers.get("authorization");
  if (!authHeader) return false;

  const baseUrl = (Deno.env.get("BUTTERBASE_URL") ?? "").replace(/\/$/, "");
  const serviceKey = Deno.env.get("BUTTERBASE_SERVICE_KEY") ?? "";
  if (!baseUrl || !serviceKey) return false;

  // 1. Resolve the caller's uid from their JWT.
  const userRes = await fetch(`${baseUrl}/auth/user`, {
    headers: { authorization: authHeader },
  });
  if (!userRes.ok) return false;
  const uid = (await userRes.json())?.id;
  if (!uid) return false;

  // 2. Service-key read of the child row, checking the doctor assignment.
  const childRes = await fetch(
    `${baseUrl}/rest/children?id=eq.${encodeURIComponent(childId)}`,
    { headers: { authorization: `Bearer ${serviceKey}` } },
  );
  if (!childRes.ok) return false;
  const rows = (await childRes.json()) as Array<{ doctor_user_id?: string }>;
  return rows.length > 0 && rows[0].doctor_user_id === uid;
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}
