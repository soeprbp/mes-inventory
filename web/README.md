# MES Inventory Web Capture

Phone-friendly manual entry app for MES inventory collection. Photos are uploaded
to private Cloudflare R2 objects through short-lived signed URLs. Metadata, notes,
and photo object keys are stored in Neon Postgres.

## Local Setup

1. Copy `.env.local.example` to `.env.local`.
2. Fill in the R2 values from the project-local Cloudflare setup.
3. Add `DATABASE_URL` from Neon.
4. Apply `db/schema.sql` to the Neon database.
5. Set `APP_PASSCODE_HASH` and `APP_SESSION_SECRET`.
6. Set `AI_PROVIDER=opencode-go`, `OPENCODE_API_KEY`, and `WORKER_SECRET`.

`APP_PASSCODE_HASH` supports `sha256:<hex>` for normal use. A `plain:<passcode>`
value is only intended for local throwaway development.

## Neon MCP

The repository-level `.mcp.json` includes Neon MCP as an optional operator tool.
It uses Neon's remote OAuth server and does not store Neon API keys in the repo.
Use it for database/project administration from an MCP client; the app runtime
still connects through `DATABASE_URL`.

## Scripts

```bash
npm run dev
npm run lint
npm run build
npm run db:push
npm run worker:analyze
```

Open `http://localhost:3000` during local development.

## Analysis Worker

The `Analyze` button enqueues a row in `ai_analysis_jobs`. The worker processes
queued rows separately so the browser request does not wait on model latency.

Local processing:

```bash
npm run worker:analyze
```

Production processing calls:

```powershell
$env:WORKER_BASE_URL="https://mesinventory.vercel.app"
npm run worker:analyze
```

The production worker endpoint requires `Authorization: Bearer <WORKER_SECRET>`.
The default OpenCode Go fallback list is:

```text
kimi-k2.6,kimi-k2.7-code,mimo-v2.5-pro,mimo-v2.5,minimax-m2.5
```
