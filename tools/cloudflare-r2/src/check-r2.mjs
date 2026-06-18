import { randomUUID } from "node:crypto";
import { ensureBucket, listBuckets } from "./cloudflare-api.mjs";
import { deleteObject, headObject, putObject } from "./r2-client.mjs";
import { getBucketName, getEnv, loadLocalEnv } from "./env.mjs";

loadLocalEnv();

function hasS3Credentials() {
  return Boolean(getEnv("R2_ACCESS_KEY_ID") && getEnv("R2_SECRET_ACCESS_KEY"));
}

async function main() {
  const bucketName = getBucketName();

  console.log(`Checking Cloudflare R2 bucket metadata for ${bucketName}...`);
  const ensureResult = await ensureBucket(bucketName);
  console.log(ensureResult.created ? "Bucket created." : "Bucket already exists.");

  const buckets = await listBuckets();
  console.log(`Visible buckets: ${buckets.length}`);

  if (!hasS3Credentials()) {
    console.log("Skipping S3 object test because R2_ACCESS_KEY_ID or R2_SECRET_ACCESS_KEY is not set.");
    return;
  }

  const key = `healthchecks/${randomUUID()}.txt`;
  console.log("Running private object put/head/delete smoke test...");
  await putObject({
    key,
    body: `mes-inventory-r2-check ${new Date().toISOString()}`,
    contentType: "text/plain"
  });
  await headObject({ key });
  await deleteObject({ key });
  console.log("R2 object smoke test completed.");
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
