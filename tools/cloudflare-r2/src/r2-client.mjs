import {
  DeleteObjectCommand,
  GetObjectCommand,
  HeadObjectCommand,
  PutObjectCommand,
  S3Client
} from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { getBucketName, getEnv, getR2Endpoint, loadLocalEnv, requireEnv } from "./env.mjs";

loadLocalEnv();

let cachedClient;

export function getR2Client() {
  requireEnv(["CLOUDFLARE_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"]);

  if (!cachedClient) {
    cachedClient = new S3Client({
      region: "auto",
      endpoint: getR2Endpoint(),
      forcePathStyle: true,
      credentials: {
        accessKeyId: getEnv("R2_ACCESS_KEY_ID"),
        secretAccessKey: getEnv("R2_SECRET_ACCESS_KEY")
      }
    });
  }

  return cachedClient;
}

export async function createPresignedPutUrl({ key, contentType, expiresInSeconds = 900, bucketName = getBucketName() }) {
  const command = new PutObjectCommand({
    Bucket: bucketName,
    Key: key,
    ContentType: contentType || "application/octet-stream"
  });

  return getSignedUrl(getR2Client(), command, { expiresIn: expiresInSeconds });
}

export async function createPresignedGetUrl({ key, expiresInSeconds = 900, bucketName = getBucketName() }) {
  const command = new GetObjectCommand({
    Bucket: bucketName,
    Key: key
  });

  return getSignedUrl(getR2Client(), command, { expiresIn: expiresInSeconds });
}

export async function headObject({ key, bucketName = getBucketName() }) {
  return getR2Client().send(new HeadObjectCommand({ Bucket: bucketName, Key: key }));
}

export async function putObject({ key, body, contentType = "application/octet-stream", bucketName = getBucketName() }) {
  return getR2Client().send(new PutObjectCommand({
    Bucket: bucketName,
    Key: key,
    Body: body,
    ContentType: contentType
  }));
}

export async function deleteObject({ key, bucketName = getBucketName() }) {
  return getR2Client().send(new DeleteObjectCommand({ Bucket: bucketName, Key: key }));
}
