import "server-only";

import { isDatabaseConfigured } from "@/lib/db";
import { isR2Configured } from "@/lib/r2";

export type RuntimeStatus = {
  databaseConfigured: boolean;
  aiConfigured: boolean;
  r2Configured: boolean;
  metadataStorage: "neon" | "local";
};

export async function getRuntimeStatus(): Promise<RuntimeStatus> {
  return {
    aiConfigured: Boolean(
      process.env.AI_PROVIDER === "opencode-go"
        ? process.env.OPENCODE_API_KEY
        : process.env.OPENAI_API_KEY,
    ),
    databaseConfigured: isDatabaseConfigured(),
    metadataStorage: isDatabaseConfigured() ? "neon" : "local",
    r2Configured: isR2Configured(),
  };
}
