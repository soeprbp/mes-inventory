import { getBucketName, getEnv, loadLocalEnv, requireEnv } from "./env.mjs";

loadLocalEnv();

const API_BASE = "https://api.cloudflare.com/client/v4";

export async function cloudflareFetch(path, options = {}) {
  requireEnv(["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"]);

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${getEnv("CLOUDFLARE_API_TOKEN")}`,
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });

  const text = await response.text();
  let payload;
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { raw: text };
  }

  if (!response.ok || payload.success === false) {
    const messages = Array.isArray(payload.errors)
      ? payload.errors.map((error) => error.message).join("; ")
      : response.statusText;
    throw new Error(`Cloudflare API request failed (${response.status}): ${messages}`);
  }

  return payload;
}

export async function listBuckets() {
  const accountId = getEnv("CLOUDFLARE_ACCOUNT_ID");
  const payload = await cloudflareFetch(`/accounts/${accountId}/r2/buckets`);
  return payload.result?.buckets || payload.result || [];
}

export async function ensureBucket(bucketName = getBucketName()) {
  const buckets = await listBuckets();
  const exists = buckets.some((bucket) => bucket.name === bucketName);
  if (exists) {
    return { bucketName, created: false };
  }

  const accountId = getEnv("CLOUDFLARE_ACCOUNT_ID");
  await cloudflareFetch(`/accounts/${accountId}/r2/buckets/${encodeURIComponent(bucketName)}`, {
    method: "PUT"
  });
  return { bucketName, created: true };
}

export async function getBucketCors(bucketName = getBucketName()) {
  const accountId = getEnv("CLOUDFLARE_ACCOUNT_ID");
  const payload = await cloudflareFetch(
    `/accounts/${accountId}/r2/buckets/${encodeURIComponent(bucketName)}/cors`
  );
  return payload.result || {};
}

export async function putBucketCors({ origins, bucketName = getBucketName() }) {
  const accountId = getEnv("CLOUDFLARE_ACCOUNT_ID");
  await cloudflareFetch(
    `/accounts/${accountId}/r2/buckets/${encodeURIComponent(bucketName)}/cors`,
    {
      method: "PUT",
      body: JSON.stringify({
        rules: [
          {
            allowed: {
              origins,
              methods: ["GET", "HEAD", "PUT"],
              headers: ["Content-Type", "Content-MD5", "x-amz-*"]
            },
            expose_headers: ["ETag"],
            max_age_seconds: 3600
          }
        ]
      })
    }
  );
  return { origins, methods: ["GET", "HEAD", "PUT"] };
}
