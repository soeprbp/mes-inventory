import "server-only";

import { DeleteObjectCommand, GetObjectCommand, PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

type UploadUrlInput = {
  key: string;
  contentType: string;
};

let client: S3Client | null = null;

function requiredEnv(name: string) {
  const value = process.env[name];

  if (!value) {
    throw new Error(`${name} is not configured.`);
  }

  return value;
}

function getR2Client() {
  client ??= new S3Client({
    endpoint:
      process.env.R2_ENDPOINT ??
      `https://${requiredEnv("CLOUDFLARE_ACCOUNT_ID")}.r2.cloudflarestorage.com`,
    region: "auto",
    credentials: {
      accessKeyId: requiredEnv("R2_ACCESS_KEY_ID"),
      secretAccessKey: requiredEnv("R2_SECRET_ACCESS_KEY"),
    },
    forcePathStyle: true,
  });

  return client;
}

export function isR2Configured() {
  return Boolean(
    process.env.CLOUDFLARE_ACCOUNT_ID &&
      process.env.R2_BUCKET_NAME &&
      process.env.R2_ACCESS_KEY_ID &&
      process.env.R2_SECRET_ACCESS_KEY,
  );
}

export function buildObjectKey(filename: string) {
  const safeName =
    filename
      .replace(/[^a-zA-Z0-9._-]/g, "-")
      .replace(/-+/g, "-")
      .slice(0, 120) || "photo";
  const today = new Date().toISOString().slice(0, 10);

  return `manual-captures/${today}/${crypto.randomUUID()}-${safeName}`;
}

export async function createPresignedUploadUrl(input: UploadUrlInput) {
  const command = new PutObjectCommand({
    Bucket: requiredEnv("R2_BUCKET_NAME"),
    Key: input.key,
    ContentType: input.contentType,
  });

  return getSignedUrl(getR2Client(), command, { expiresIn: 300 });
}

export async function createPresignedReadUrl(key: string) {
  const command = new GetObjectCommand({
    Bucket: requiredEnv("R2_BUCKET_NAME"),
    Key: key,
  });

  return getSignedUrl(getR2Client(), command, { expiresIn: 300 });
}

export async function deleteObject(key: string) {
  const command = new DeleteObjectCommand({
    Bucket: requiredEnv("R2_BUCKET_NAME"),
    Key: key,
  });

  await getR2Client().send(command);
}
