import { NextResponse } from "next/server";
import { z } from "zod";
import { enqueueAssetPhotoAnalysis } from "@/lib/ai-analysis";
import { getSession } from "@/lib/auth";
import { isDatabaseConfigured } from "@/lib/db";

const analyzeSchema = z.object({
  assetId: z.string().min(1).max(120),
  objectKey: z.string().min(1).max(512),
});

export async function POST(request: Request) {
  const session = await getSession();

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (!isDatabaseConfigured()) {
    return NextResponse.json(
      { error: "Neon database is required for AI analysis." },
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

  const parsed = analyzeSchema.safeParse(await request.json());

  if (!parsed.success) {
    return NextResponse.json(
      { error: "Invalid analysis request." },
      { status: 400 },
    );
  }

  try {
    const job = await enqueueAssetPhotoAnalysis(parsed.data);
    return NextResponse.json({ job }, { status: 202 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Photo analysis failed.";

    return NextResponse.json({ error: message }, { status: 500 });
  }
}
