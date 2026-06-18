import "server-only";

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import type { AssetInput, AssetSummary } from "@/lib/assets";

const dataDir = path.join(process.cwd(), "data");
const dataFile = path.join(dataDir, "field-test-assets.json");

type LocalStoredAsset = AssetSummary & {
  manufacturer: string | null;
  model: string | null;
  serialNumber: string | null;
};

async function readAssets(): Promise<LocalStoredAsset[]> {
  try {
    const raw = await readFile(dataFile, "utf8");
    return JSON.parse(raw) as LocalStoredAsset[];
  } catch (error) {
    if (
      error &&
      typeof error === "object" &&
      "code" in error &&
      error.code === "ENOENT"
    ) {
      return [];
    }

    throw error;
  }
}

async function writeAssets(assets: LocalStoredAsset[]) {
  await mkdir(dataDir, { recursive: true });
  await writeFile(dataFile, `${JSON.stringify(assets, null, 2)}\n`, "utf8");
}

function optional(value?: string) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

export async function getRecentLocalAssets(): Promise<AssetSummary[]> {
  const assets = await readAssets();

  return assets
    .toSorted((left, right) => right.createdAt.localeCompare(left.createdAt))
    .slice(0, 20);
}

export async function createLocalAssetWithNotesAndPhotos(input: AssetInput) {
  const assets = await readAssets();
  const assetId = crypto.randomUUID();
  const note = optional(input.note);
  const stored: LocalStoredAsset = {
    id: assetId,
    label: input.label.trim(),
    hostname: optional(input.hostname),
    location: optional(input.location),
    assetTag: optional(input.assetTag),
    manufacturer: optional(input.manufacturer),
    model: optional(input.model),
    serialNumber: optional(input.serialNumber),
    equipmentTypeGuess: optional(input.equipmentTypeGuess),
    createdAt: new Date().toISOString(),
    noteCount: note ? 1 : 0,
    notes: note ? [note] : [],
    latestAnalysis: null,
    photoCount: input.photos.length,
    photos: input.photos.map((photo) => ({
      id: null,
      key: photo.key,
      filename: photo.filename,
      contentType: photo.contentType,
      sizeBytes: photo.sizeBytes,
      caption: optional(photo.caption),
    })),
    storage: "local",
  };

  assets.push(stored);
  await writeAssets(assets);

  return { id: assetId, label: input.label.trim() };
}
