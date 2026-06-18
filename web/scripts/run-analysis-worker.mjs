import { readFile } from "node:fs/promises";

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
  const env = parseEnv(await readFile(".env.local", "utf8"));
  const baseUrl = process.env.WORKER_BASE_URL ?? "http://127.0.0.1:3000";
  const workerSecret = process.env.WORKER_SECRET ?? env.WORKER_SECRET;
  const response = await fetch(`${baseUrl}/api/worker/analyze?limit=3`, {
    headers: workerSecret ? { authorization: `Bearer ${workerSecret}` } : {},
    method: "POST",
  });
  const body = await response.text();

  if (!response.ok) {
    throw new Error(`worker status ${response.status}: ${body}`);
  }

  console.log(body);
}

main().catch((error) => {
  console.error(`worker_run=fail ${error.message}`);
  process.exitCode = 1;
});
