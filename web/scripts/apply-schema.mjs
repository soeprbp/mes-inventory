import { readFile } from "node:fs/promises";
import path from "node:path";
import { neon } from "@neondatabase/serverless";

const envPath = path.join(process.cwd(), ".env.local");
const schemaPath = path.join(process.cwd(), "db", "schema.sql");

function parseEnv(raw) {
  return Object.fromEntries(
    raw
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#"))
      .map((line) => {
        const index = line.indexOf("=");
        return [line.slice(0, index), line.slice(index + 1)];
      }),
  );
}

async function main() {
  const env = parseEnv(await readFile(envPath, "utf8"));
  const databaseUrl = env.DATABASE_URL || process.env.DATABASE_URL;

  if (!databaseUrl) {
    throw new Error("DATABASE_URL is missing from web/.env.local.");
  }

  const sql = neon(databaseUrl);
  const schema = await readFile(schemaPath, "utf8");

  for (const statement of schema
    .split(/;\s*(?:\r?\n|$)/)
    .map((item) => item.trim())
    .filter(Boolean)) {
    await sql.query(`${statement};`);
  }

  console.log("schema_apply=pass");
}

main().catch((error) => {
  console.error(`schema_apply=fail ${error.message}`);
  process.exitCode = 1;
});
