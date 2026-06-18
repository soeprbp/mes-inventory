#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { ensureBucket, getBucketCors, listBuckets, putBucketCors } from "./cloudflare-api.mjs";
import { createPresignedGetUrl, createPresignedPutUrl } from "./r2-client.mjs";
import { getBucketName, loadLocalEnv, parseCorsOrigins } from "./env.mjs";

loadLocalEnv();

const server = new McpServer({
  name: "mes-inventory-cloudflare-r2",
  version: "0.1.0"
});

function jsonText(value) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(value, null, 2)
      }
    ]
  };
}

server.tool("r2_list_buckets", "List R2 buckets visible to the configured Cloudflare API token.", {}, async () => {
  const buckets = await listBuckets();
  return jsonText({ buckets });
});

server.tool(
  "r2_ensure_bucket",
  "Create the configured private R2 bucket if it does not already exist.",
  {
    bucketName: z.string().optional().describe("Bucket name. Defaults to R2_BUCKET_NAME.")
  },
  async ({ bucketName }) => {
    const result = await ensureBucket(bucketName || getBucketName());
    return jsonText(result);
  }
);

server.tool(
  "r2_presign_put",
  "Create a short-lived presigned PUT URL for direct browser upload.",
  {
    key: z.string().min(1),
    contentType: z.string().optional(),
    expiresInSeconds: z.number().int().min(60).max(3600).optional()
  },
  async ({ key, contentType, expiresInSeconds }) => {
    const url = await createPresignedPutUrl({ key, contentType, expiresInSeconds });
    return jsonText({ key, method: "PUT", expiresInSeconds: expiresInSeconds || 900, url });
  }
);

server.tool(
  "r2_presign_get",
  "Create a short-lived presigned GET URL for private object viewing.",
  {
    key: z.string().min(1),
    expiresInSeconds: z.number().int().min(60).max(3600).optional()
  },
  async ({ key, expiresInSeconds }) => {
    const url = await createPresignedGetUrl({ key, expiresInSeconds });
    return jsonText({ key, method: "GET", expiresInSeconds: expiresInSeconds || 900, url });
  }
);

server.tool("r2_get_bucket_cors", "Read the configured R2 bucket CORS policy.", {}, async () => {
  const cors = await getBucketCors();
  return jsonText(cors);
});

server.tool(
  "r2_put_bucket_cors",
  "Set the configured R2 bucket CORS policy for presigned upload/read URLs.",
  {
    origins: z.array(z.string()).optional().describe("Allowed origins. Defaults to R2_CORS_ORIGINS.")
  },
  async ({ origins }) => {
    const selectedOrigins = origins?.length ? origins : parseCorsOrigins();
    await putBucketCors({ origins: selectedOrigins });
    return jsonText({ origins: selectedOrigins, methods: ["GET", "HEAD", "PUT"] });
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
