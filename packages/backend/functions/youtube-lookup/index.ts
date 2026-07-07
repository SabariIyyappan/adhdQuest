/**
 * Butterbase serverless function (Deno) — YouTube micro-lesson lookup.
 * Called by Pipeline 2. Given a concept and the child's remaining attention window,
 * returns the single best short video matched to concept + grade (plan §5, §6 Feature 2).
 *
 * Deploy: `butterbase functions deploy youtube-lookup`
 */

import type { VideoRecommendation } from "@adhdquest/contracts";

interface LookupRequest {
  concept_tag: string;
  remaining_attention_seconds: number;
  grade_level: number;
}

const YOUTUBE_API = "https://www.googleapis.com/youtube/v3/search";

Deno.serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return json({ error: "POST only" }, 405);
  }

  const body = (await req.json()) as LookupRequest;

  // Too little attention left for a video to help — signal "skip" (plan §6 Feature 2).
  if (body.remaining_attention_seconds < 120) {
    return json({ video: null, reason: "attention_too_low" });
  }

  const maxDurationBucket =
    body.remaining_attention_seconds <= 300 ? "short" : "medium"; // <2min : <4min

  const params = new URLSearchParams({
    key: Deno.env.get("YOUTUBE_API_KEY") ?? "",
    part: "snippet",
    q: `${body.concept_tag} for grade ${body.grade_level} kids`,
    type: "video",
    videoDuration: maxDurationBucket,
    videoEmbeddable: "true",
    safeSearch: "strict",
    order: "relevance",
    maxResults: "1",
  });

  const res = await fetch(`${YOUTUBE_API}?${params}`);
  if (!res.ok) {
    // Fallback so a demo never hard-fails on quota (plan §10 risk register).
    return json({ video: mockVideo(body.concept_tag), reason: "api_error_fallback" });
  }

  const data = await res.json();
  const item = data.items?.[0];
  if (!item) return json({ video: null, reason: "no_results" });

  const video: VideoRecommendation = {
    youtube_id: item.id.videoId,
    title: item.snippet.title,
    thumbnail_url: item.snippet.thumbnails?.medium?.url ?? "",
    duration_seconds: maxDurationBucket === "short" ? 120 : 240, // upper bound of bucket
    url: `https://www.youtube.com/watch?v=${item.id.videoId}`,
  };
  return json({ video });
});

function mockVideo(concept: string): VideoRecommendation {
  return {
    youtube_id: "dQw4w9WgXcQ",
    title: `Understanding ${concept} — visual explainer`,
    thumbnail_url: "",
    duration_seconds: 150,
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  };
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}
