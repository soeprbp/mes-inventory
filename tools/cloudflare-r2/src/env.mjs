import fs from "node:fs";
import path from "node:path";

export function findRepoRoot(startDir = process.cwd()) {
  let current = path.resolve(startDir);
  while (true) {
    if (fs.existsSync(path.join(current, ".git")) || fs.existsSync(path.join(current, ".env.example"))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      return path.resolve(startDir);
    }
    current = parent;
  }
}

function parseEnvLine(line) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith("#")) {
    return null;
  }

  const index = trimmed.indexOf("=");
  if (index === -1) {
    return null;
  }

  const key = trimmed.slice(0, index).trim();
  let value = trimmed.slice(index + 1).trim();
  if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
    value = value.slice(1, -1);
  }
  return [key, value];
}

export function loadLocalEnv(startDir = process.cwd()) {
  const repoRoot = findRepoRoot(startDir);
  const envPath = path.join(repoRoot, ".env.local");
  if (!fs.existsSync(envPath)) {
    return { repoRoot, envPath, loaded: false };
  }

  const content = fs.readFileSync(envPath, "utf8");
  for (const line of content.split(/\r?\n/)) {
    const parsed = parseEnvLine(line);
    if (!parsed) {
      continue;
    }
    const [key, value] = parsed;
    if (process.env[key] === undefined) {
      process.env[key] = value;
    }
  }

  return { repoRoot, envPath, loaded: true };
}

export function getEnv(name, fallback = undefined) {
  const value = process.env[name];
  if (value === undefined || value === "") {
    return fallback;
  }
  return value;
}

export function requireEnv(names) {
  const missing = names.filter((name) => !getEnv(name));
  if (missing.length) {
    throw new Error(`Missing required environment variables: ${missing.join(", ")}`);
  }
}

export function getR2Endpoint() {
  const configured = getEnv("R2_ENDPOINT");
  if (configured) {
    return configured.replace(/\/$/, "");
  }

  const accountId = getEnv("CLOUDFLARE_ACCOUNT_ID");
  if (!accountId) {
    return undefined;
  }

  return `https://${accountId}.r2.cloudflarestorage.com`;
}

export function getBucketName() {
  return getEnv("R2_BUCKET_NAME", "mes-inventory-photos");
}

export function parseCorsOrigins() {
  return getEnv("R2_CORS_ORIGINS", "http://localhost:3000")
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);
}
