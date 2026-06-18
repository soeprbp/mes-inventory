import { NextResponse } from "next/server";
import { processQueuedAnalysisJobs } from "@/lib/ai-analysis";
import { isDatabaseConfigured } from "@/lib/db";

function isAuthorized(request: Request) {
  const workerSecret = process.env.WORKER_SECRET;

  if (!workerSecret) {
    return process.env.NODE_ENV !== "production";
  }

  return request.headers.get("authorization") === `Bearer ${workerSecret}`;
}

export async function POST(request: Request) {
  if (!isAuthorized(request)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (!isDatabaseConfigured()) {
    return NextResponse.json(
      { error: "Neon database is required for worker processing." },
      { status: 503 },
    );
  }

  if (
    process.env.AI_PROVIDER === "opencode-go"
      ? !process.env.OPENCODE_API_KEY
      : !process.env.OPENAI_API_KEY
  ) {
    return NextResponse.json(
      { error: "AI provider credentials are not configured yet." },
      { status: 503 },
    );
  }

  const url = new URL(request.url);
  const limit = Math.min(Number(url.searchParams.get("limit") ?? 3), 5);
  const result = await processQueuedAnalysisJobs(limit);

  return NextResponse.json(result);
}
