# Serverless functions (Deno, deployed to Butterbase)

Two on-demand functions owned by Person A.

| Function        | Caller                     | Purpose                                                                 |
|-----------------|----------------------------|-------------------------------------------------------------------------|
| `youtube-lookup`| Pipeline 2 (replan)        | concept + remaining attention window → single best short YouTube video  |
| `cognee-qa`     | Frontend doctor dashboard  | doctor question → Cognee `GRAPH_COMPLETION` cited answer for that child  |

## Env each function needs (set in the Butterbase functions dashboard)

- `youtube-lookup`: `YOUTUBE_API_KEY`
- `cognee-qa`: `COGNEE_API_URL`, `BUTTERBASE_URL`, `BUTTERBASE_SERVICE_KEY`

## Local typecheck

```bash
cd packages/backend/functions
deno task check
```

## Deploy

```bash
cd packages/backend/functions
deno task deploy:youtube
deno task deploy:cognee-qa
```

`youtube-lookup` degrades gracefully: on quota/API error it returns a mock video so a
live demo never hard-fails (plan §10 risk register). `cognee-qa` enforces the
doctor-assignment check before spending a Cognee call — defense in depth beyond RLS.
