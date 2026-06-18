import "server-only";

import OpenAI from "openai";
import { getSql } from "@/lib/db";
import { createPresignedReadUrl } from "@/lib/r2";
import type { EquipmentPhotoAnalysis } from "@/lib/assets";

const promptVersion = "equipment-photo-v1";
const defaultOpenCodeModels = [
  "kimi-k2.6",
  "kimi-k2.7-code",
  "mimo-v2.5-pro",
  "mimo-v2.5",
  "minimax-m2.5",
];

type AnalysisJob = {
  id: string;
  asset_id: string;
  photo_id: string | null;
  object_key: string;
};

const equipmentAnalysisSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    primaryIdentification: {
      type: "string",
      description:
        "Best concise identification of the visible equipment or scene.",
    },
    equipmentCategory: {
      type: "string",
      description:
        "Category such as PLC, HMI, industrial PC, workstation, network switch, cabinet, sensor, drive, or unknown.",
    },
    manufacturer: {
      type: ["string", "null"],
      description: "Visible or inferred manufacturer, null if not visible.",
    },
    model: {
      type: ["string", "null"],
      description: "Visible model, family, or part number, null if not visible.",
    },
    serialNumber: {
      type: ["string", "null"],
      description: "Visible serial number or service tag, null if not visible.",
    },
    visibleText: {
      type: "array",
      items: { type: "string" },
      description: "Important readable labels, tags, stickers, ports, or text.",
    },
    confidence: {
      type: "string",
      enum: ["low", "medium", "high"],
    },
    observations: {
      type: "array",
      items: { type: "string" },
      description: "Short visual observations relevant to MES inventory.",
    },
    suggestedFollowUp: {
      type: "array",
      items: { type: "string" },
      description: "Practical next capture or inspection steps.",
    },
  },
  required: [
    "primaryIdentification",
    "equipmentCategory",
    "manufacturer",
    "model",
    "serialNumber",
    "visibleText",
    "confidence",
    "observations",
    "suggestedFollowUp",
  ],
} as const;

function getOpenAI() {
  if (!process.env.OPENAI_API_KEY) {
    throw new Error("OPENAI_API_KEY is not configured.");
  }

  return new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

function getPromptText() {
  return [
    "Identify this MES/industrial equipment photo.",
    "Focus on PLCs, HMIs, industrial PCs, workstations, network gear, cabinets, drives, sensors, labels, manufacturer names, model numbers, serial/service tags, and practical follow-up photos needed.",
    "Be careful: if text is unreadable or a part is uncertain, say so and lower confidence.",
    "Return only valid JSON matching this schema:",
    JSON.stringify(equipmentAnalysisSchema),
  ].join(" ");
}

function parseJsonContent(content: string) {
  const trimmed = content.trim();
  const withoutFence = trimmed
    .replace(/^```json\s*/i, "")
    .replace(/^```\s*/i, "")
    .replace(/\s*```$/i, "")
    .trim();

  return JSON.parse(withoutFence) as EquipmentPhotoAnalysis;
}

function getOpenCodeModelFallbacks() {
  const configured =
    process.env.OPENCODE_GO_MODELS ??
    process.env.OPENCODE_GO_MODEL ??
    defaultOpenCodeModels.join(",");

  return configured
    .split(",")
    .map((model) => model.trim())
    .filter(Boolean);
}

async function analyzeWithOpenCodeGo(imageUrl: string, model: string) {
  if (!process.env.OPENCODE_API_KEY) {
    throw new Error("OPENCODE_API_KEY is not configured.");
  }

  const response = await fetch(
    "https://opencode.ai/zen/go/v1/chat/completions",
    {
      body: JSON.stringify({
        model,
        messages: [
          {
            role: "user",
            content: [
              { type: "text", text: getPromptText() },
              { type: "image_url", image_url: { url: imageUrl } },
            ],
          },
        ],
        response_format: { type: "json_object" },
        temperature: 0.1,
      }),
      headers: {
        authorization: `Bearer ${process.env.OPENCODE_API_KEY}`,
        "content-type": "application/json",
      },
      method: "POST",
    },
  );

  const body = (await response.json()) as {
    choices?: Array<{ message?: { content?: string } }>;
    error?: { message?: string };
  };

  if (!response.ok) {
    throw new Error(
      `OpenCode Go ${response.status}: ${body.error?.message ?? "request failed"}`,
    );
  }

  const content = body.choices?.[0]?.message?.content;

  if (!content) {
    throw new Error("OpenCode Go returned no analysis content.");
  }

  return {
    model: `opencode-go/${model}`,
    result: parseJsonContent(content),
  };
}

async function analyzeWithOpenCodeFallbacks(imageUrl: string) {
  const errors: string[] = [];

  for (const model of getOpenCodeModelFallbacks()) {
    try {
      return await analyzeWithOpenCodeGo(imageUrl, model);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "analysis request failed";
      errors.push(`${model}: ${message}`);
    }
  }

  throw new Error(`All OpenCode Go models failed. ${errors.join(" | ")}`);
}

async function analyzeWithOpenAI(imageUrl: string) {
  const model = process.env.OPENAI_VISION_MODEL || "gpt-5.5";
  const response = await getOpenAI().responses.create({
    model,
    input: [
      {
        role: "user",
        content: [
          {
            type: "input_text",
            text: getPromptText(),
          },
          {
            type: "input_image",
            detail: "auto",
            image_url: imageUrl,
          },
        ],
      },
    ],
    text: {
      format: {
        type: "json_schema",
        name: "equipment_photo_analysis",
        strict: true,
        schema: equipmentAnalysisSchema,
      },
    },
  });

  return {
    model,
    result: JSON.parse(response.output_text) as EquipmentPhotoAnalysis,
  };
}

export async function enqueueAssetPhotoAnalysis(input: {
  assetId: string;
  objectKey: string;
}) {
  const sql = getSql();
  const photos = (await sql`
    select id, asset_id, object_key, filename, content_type
    from photos
    where asset_id = ${input.assetId}
      and object_key = ${input.objectKey}
    limit 1
  `) as Array<{ id: string }>;
  const [photo] = photos;

  if (!photo) {
    throw new Error("Photo was not found for this asset.");
  }

  const jobId = crypto.randomUUID();
  const requestedModel =
    process.env.AI_PROVIDER === "opencode-go"
      ? `opencode-go/${getOpenCodeModelFallbacks().join(" -> ")}`
      : process.env.OPENAI_VISION_MODEL || "gpt-5.5";

  await sql`
    insert into ai_analysis_jobs (
      id,
      asset_id,
      photo_id,
      object_key,
      status,
      model,
      prompt_version
    )
    values (
      ${jobId},
      ${input.assetId},
      ${photo.id},
      ${input.objectKey},
      'queued',
      ${requestedModel},
      ${promptVersion}
    )
  `;

  return { id: jobId, status: "queued" };
}

async function claimQueuedAnalysisJob(): Promise<AnalysisJob | null> {
  const sql = getSql();
  const rows = (await sql`
    update ai_analysis_jobs
    set status = 'running',
        attempts = attempts + 1,
        updated_at = now()
    where id = (
      select id
      from ai_analysis_jobs
      where status = 'queued'
      order by created_at asc
      limit 1
      for update skip locked
    )
    returning id, asset_id, photo_id, object_key
  `) as AnalysisJob[];

  return rows[0] ?? null;
}

async function processAnalysisJob(job: AnalysisJob) {
  const sql = getSql();

  try {
    const imageUrl = await createPresignedReadUrl(job.object_key);
    const analysis =
      process.env.AI_PROVIDER === "opencode-go"
        ? await analyzeWithOpenCodeFallbacks(imageUrl)
        : await analyzeWithOpenAI(imageUrl);

    await sql`
      update ai_analysis_jobs
      set status = 'succeeded',
          model = ${analysis.model},
          result = ${JSON.stringify(analysis.result)}::jsonb,
          updated_at = now()
      where id = ${job.id}
    `;

    return { id: job.id, status: "succeeded", result: analysis.result };
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Photo analysis failed.";

    await sql`
      update ai_analysis_jobs
      set status = 'failed',
          error = ${message},
          updated_at = now()
      where id = ${job.id}
    `;

    return { id: job.id, status: "failed", error: message };
  }
}

export async function processQueuedAnalysisJobs(limit = 3) {
  const processed: Array<{
    id: string;
    status: string;
    result?: EquipmentPhotoAnalysis;
    error?: string;
  }> = [];

  for (let index = 0; index < limit; index++) {
    const job = await claimQueuedAnalysisJob();

    if (!job) {
      break;
    }

    processed.push(await processAnalysisJob(job));
  }

  return { processed };
}
