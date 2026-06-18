import { NextResponse } from "next/server";
import { z } from "zod";
import { getSession } from "@/lib/auth";
import { buildObjectKey, createPresignedUploadUrl } from "@/lib/r2";

const uploadRequestSchema = z.object({
  filename: z.string().min(1).max(180),
  contentType: z.string().min(3).max(120).startsWith("image/"),
  sizeBytes: z.number().int().positive().max(25 * 1024 * 1024),
});

export async function POST(request: Request) {
  const session = await getSession();

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const parsed = uploadRequestSchema.safeParse(await request.json());

  if (!parsed.success) {
    return NextResponse.json(
      { error: "Invalid upload request" },
      { status: 400 },
    );
  }

  const key = buildObjectKey(parsed.data.filename);
  const uploadUrl = await createPresignedUploadUrl({
    key,
    contentType: parsed.data.contentType,
  });

  return NextResponse.json({
    key,
    uploadUrl,
    expiresInSeconds: 300,
  });
}
