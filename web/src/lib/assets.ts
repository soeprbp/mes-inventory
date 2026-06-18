import "server-only";

import { getSql, isDatabaseConfigured } from "@/lib/db";
import {
  createLocalAssetWithNotesAndPhotos,
  getRecentLocalAssets,
} from "@/lib/local-store";

export type PhotoSummary = {
  id: string | null;
  key: string;
  filename: string;
  contentType: string;
  sizeBytes: number;
  caption: string | null;
};

export type AnalysisResult = {
  id: string;
  status: string;
  model: string | null;
  result: EquipmentPhotoAnalysis | null;
  error: string | null;
  attempts: number;
  createdAt: string;
};

export type EquipmentPhotoAnalysis = {
  primaryIdentification: string;
  equipmentCategory: string;
  manufacturer: string | null;
  model: string | null;
  serialNumber: string | null;
  visibleText: string[];
  confidence: "low" | "medium" | "high";
  observations: string[];
  suggestedFollowUp: string[];
};

export type AssetSummary = {
  id: string;
  label: string;
  hostname: string | null;
  location: string | null;
  assetTag: string | null;
  equipmentTypeGuess: string | null;
  createdAt: string;
  photoCount: number;
  noteCount: number;
  notes: string[];
  photos: PhotoSummary[];
  latestAnalysis: AnalysisResult | null;
  storage: "neon" | "local";
};

export type AssetInput = {
  label: string;
  hostname?: string;
  location?: string;
  assetTag?: string;
  manufacturer?: string;
  model?: string;
  serialNumber?: string;
  equipmentTypeGuess?: string;
  note?: string;
  photos: Array<{
    key: string;
    filename: string;
    contentType: string;
    sizeBytes: number;
    caption?: string;
  }>;
};

function optional(value?: string) {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

export async function getRecentAssets(): Promise<AssetSummary[]> {
  if (!isDatabaseConfigured()) {
    return getRecentLocalAssets();
  }

  const sql = getSql();
  const rows = await sql`
    select
      a.id,
      a.label,
      a.hostname,
      a.location,
      a.asset_tag as "assetTag",
      a.equipment_type_guess as "equipmentTypeGuess",
      a.created_at as "createdAt",
      count(distinct p.id)::int as "photoCount",
      count(distinct n.id)::int as "noteCount",
      coalesce(
        array_remove(array_agg(distinct n.body), null),
        array[]::text[]
      ) as notes,
      coalesce(
        jsonb_agg(
          distinct jsonb_build_object(
            'key', p.object_key,
            'id', p.id,
            'filename', p.filename,
            'contentType', p.content_type,
            'sizeBytes', p.size_bytes,
            'caption', p.caption
          )
        ) filter (where p.id is not null),
        '[]'::jsonb
      ) as photos,
      'neon' as storage,
      (
        select jsonb_build_object(
          'id', j.id,
          'status', j.status,
          'model', j.model,
          'result', j.result,
          'error', j.error,
          'attempts', j.attempts,
          'createdAt', j.created_at
        )
        from ai_analysis_jobs j
        where j.asset_id = a.id
        order by j.created_at desc
        limit 1
      ) as "latestAnalysis"
    from assets a
    left join photos p on p.asset_id = a.id
    left join notes n on n.asset_id = a.id
    group by a.id
    order by a.created_at desc
    limit 20
  `;

  return rows as AssetSummary[];
}

export async function createAssetWithNotesAndPhotos(input: AssetInput) {
  if (!isDatabaseConfigured()) {
    return createLocalAssetWithNotesAndPhotos(input);
  }

  const sql = getSql();
  const assetId = crypto.randomUUID();

  await sql`
    insert into assets (
      id,
      label,
      hostname,
      location,
      asset_tag,
      manufacturer,
      model,
      serial_number,
      equipment_type_guess,
      source
    )
    values (
      ${assetId},
      ${input.label.trim()},
      ${optional(input.hostname)},
      ${optional(input.location)},
      ${optional(input.assetTag)},
      ${optional(input.manufacturer)},
      ${optional(input.model)},
      ${optional(input.serialNumber)},
      ${optional(input.equipmentTypeGuess)},
      'manual'
    )
  `;

  if (optional(input.note)) {
    await sql`
      insert into notes (id, asset_id, body)
      values (${crypto.randomUUID()}, ${assetId}, ${input.note!.trim()})
    `;
  }

  for (const photo of input.photos) {
    await sql`
      insert into photos (
        id,
        asset_id,
        object_key,
        filename,
        content_type,
        size_bytes,
        caption
      )
      values (
        ${crypto.randomUUID()},
        ${assetId},
        ${photo.key},
        ${photo.filename},
        ${photo.contentType},
        ${photo.sizeBytes},
        ${optional(photo.caption)}
      )
    `;
  }

  return { id: assetId, label: input.label.trim() };
}
