import { NextResponse } from "next/server";
import { z } from "zod";
import { getSession } from "@/lib/auth";
import { createPresignedReadUrl } from "@/lib/r2";

const readRequestSchema = z.object({
  key: z.string().min(1).max(512),
});

export async function POST(request: Request) {
  const session = await getSession();

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const parsed = readRequestSchema.safeParse(await request.json());

  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid object key" }, { status: 400 });
  }

  const url = await createPresignedReadUrl(parsed.data.key);

  return NextResponse.json({
    url,
    expiresInSeconds: 300,
  });
}
