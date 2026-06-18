import { parseCorsOrigins } from "./env.mjs";
import { putBucketCors } from "./cloudflare-api.mjs";

async function main() {
  const origins = parseCorsOrigins();
  if (!origins.length) {
    throw new Error("R2_CORS_ORIGINS must contain at least one origin.");
  }

  await putBucketCors({ origins });
  console.log(`R2 CORS configured for ${origins.length} origin(s).`);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
