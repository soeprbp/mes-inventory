import { NextResponse } from "next/server";
import { z } from "zod";
import { createAssetWithNotesAndPhotos, getRecentAssets } from "@/lib/assets";
import { getSession } from "@/lib/auth";
import { getRuntimeStatus } from "@/lib/runtime-status";

const photoSchema = z.object({
  key: z.string().min(1).max(512),
  filename: z.string().min(1).max(180),
  contentType: z.string().min(3).max(120),
  sizeBytes: z.number().int().positive().max(25 * 1024 * 1024),
  caption: z.string().max(500).optional(),
});

const assetSchema = z.object({
  label: z.string().min(1).max(160),
  hostname: z.string().max(160).optional(),
  location: z.string().max(160).optional(),
  assetTag: z.string().max(120).optional(),
  manufacturer: z.string().max(120).optional(),
  model: z.string().max(120).optional(),
  serialNumber: z.string().max(120).optional(),
  equipmentTypeGuess: z.string().max(120).optional(),
  note: z.string().max(4000).optional(),
  photos: z.array(photoSchema).max(12).default([]),
});

export async function GET() {
  const session = await getSession();

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  return NextResponse.json({
    assets: await getRecentAssets(),
    ...(await getRuntimeStatus()),
  });
}

export async function POST(request: Request) {
  const session = await getSession();

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const parsed = assetSchema.safeParse(await request.json());

  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid asset entry" }, { status: 400 });
  }

  const asset = await createAssetWithNotesAndPhotos(parsed.data);
  return NextResponse.json({ asset }, { status: 201 });
}
