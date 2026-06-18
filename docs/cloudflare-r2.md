# Cloudflare R2 Project Setup

This project uses Cloudflare R2 Standard storage for uploaded equipment photos and files. R2 stores the binary objects; Neon stores metadata such as object key, file name, content type, size, caption, and asset linkage.

## Credentials

Use `.env.example` as the template and create a local `.env.local` for development. Do not commit `.env.local`.

Required values:

- `CLOUDFLARE_ACCOUNT_ID`: Cloudflare account ID.
- `CLOUDFLARE_API_TOKEN`: account API token for bucket management.
- `R2_BUCKET_NAME`: default bucket, `mes-inventory-photos`.
- `R2_ACCESS_KEY_ID`: R2 S3-compatible access key ID.
- `R2_SECRET_ACCESS_KEY`: R2 S3-compatible secret access key.
- `R2_ENDPOINT`: optional; defaults to `https://<CLOUDFLARE_ACCOUNT_ID>.r2.cloudflarestorage.com`.
- `R2_CORS_ORIGINS`: comma-separated browser origins allowed to use presigned URLs.
- `DATABASE_URL`: Neon Postgres connection string for metadata.
- `APP_PASSCODE_HASH`: app login passcode hash, preferably `sha256:<hex>`.
- `APP_SESSION_SECRET`: random value used to sign app sessions.
- `AI_PROVIDER`: current photo analysis provider. The beta uses `opencode-go`.
- `OPENCODE_API_KEY`: OpenCode Go API key for the analysis worker.
- `OPENCODE_GO_MODELS`: comma-separated model fallback list.
- `WORKER_SECRET`: bearer token for protected worker endpoint calls.

The Cloudflare token values are stored outside the repo. If credentials are copied from Mem, do not paste them into tracked files, issue text, or commit messages.

## MCP

The repo includes `.mcp.json` with Cloudflare and Neon entries:

- `cloudflare-api`: Cloudflare's managed remote MCP endpoint at `https://mcp.cloudflare.com/mcp`. It uses OAuth when the MCP client connects.
- `cloudflare-r2-local`: a local stdio MCP server in `tools/cloudflare-r2` that reads `.env.local` and exposes focused R2 helpers.
- `neon`: Neon's remote OAuth MCP endpoint via `mcp-remote`.

Install local MCP dependencies:

```powershell
cd tools\cloudflare-r2
npm install
```

Run the local server manually for a smoke check:

```powershell
npm run mcp
```

## R2 Setup

Create or verify the private Standard storage bucket:

```powershell
cd tools\cloudflare-r2
npm run check
```

Configure CORS for local development:

```powershell
cd tools\cloudflare-r2
$env:R2_CORS_ORIGINS="http://localhost:3000"
npm run configure-cors
```

When a Vercel production domain is known, append it to `R2_CORS_ORIGINS`, for example:

```powershell
$env:R2_CORS_ORIGINS="http://localhost:3000,https://mes-inventory.vercel.app"
npm run configure-cors
```

## App Integration Pattern

The hosted app should not upload images through Neon or store image bytes in Postgres.

1. Authenticated route asks the server-only R2 helper for a short-lived PUT URL.
2. Browser uploads directly to R2 with that URL.
3. App writes object metadata to Neon.
4. Authenticated photo view asks for a short-lived GET URL by object key.
5. Analysis worker fetches images through short-lived GET URLs; it never stores
   image bytes in Neon.

Objects remain private by default. Do not add public bucket access unless the product decision changes.

The Next.js app in `web/` has its own `.env.local.example` because Next reads
local env files from the app directory. Do not commit `web/.env.local`.
