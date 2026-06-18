import { logoutAction } from "@/app/actions";
import { AnalyzePhotoButton } from "@/components/analyze-photo-button";
import { CaptureForm } from "@/components/capture-form";
import { PhotoOpenButton } from "@/components/photo-open-button";
import type { AssetSummary } from "@/lib/assets";
import type { RuntimeStatus } from "@/lib/runtime-status";
import { Camera, Database, HardDrive, LogOut, Server } from "lucide-react";

type CaptureWorkspaceProps = {
  assets: AssetSummary[];
  status: RuntimeStatus;
};

function StatusPill({
  ok,
  label,
}: {
  ok: boolean;
  label: string;
}) {
  return (
    <span
      className={[
        "inline-flex h-8 items-center rounded-md border px-2.5 text-xs font-semibold",
        ok
          ? "border-emerald-300 bg-emerald-50 text-emerald-800"
          : "border-amber-300 bg-amber-50 text-amber-900",
      ].join(" ")}
    >
      {label}
    </span>
  );
}

export function CaptureWorkspace({ assets, status }: CaptureWorkspaceProps) {
  return (
    <main className="min-h-dvh bg-stone-100 text-zinc-950">
      <header className="border-b border-zinc-300 bg-white">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
              MES Inventory
            </p>
            <h1 className="text-xl font-semibold">Field capture</h1>
          </div>
          <form action={logoutAction}>
            <button
              className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-zinc-300 bg-white text-zinc-700 transition hover:bg-zinc-100"
              title="Sign out"
              type="submit"
            >
              <LogOut aria-hidden="true" className="h-4 w-4" />
              <span className="sr-only">Sign out</span>
            </button>
          </form>
        </div>
      </header>

      <div className="mx-auto grid w-full max-w-6xl gap-4 px-4 py-4 sm:px-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <section className="rounded-md border border-zinc-300 bg-white p-4 shadow-sm sm:p-5">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-zinc-950 text-white">
              <Camera aria-hidden="true" className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">New equipment entry</h2>
              <p className="text-sm text-zinc-600">
                Photos stay in private R2 storage; notes and metadata use the
                active storage mode.
              </p>
            </div>
          </div>
          <CaptureForm databaseConfigured={status.databaseConfigured} />
        </section>

        <aside className="space-y-4">
          <section className="rounded-md border border-zinc-300 bg-white p-4 shadow-sm">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-zinc-800">
              <Server aria-hidden="true" className="h-4 w-4" />
              Runtime
            </h2>
            <div className="flex flex-wrap gap-2">
              <StatusPill
                label={status.r2Configured ? "R2 ready" : "R2 env missing"}
                ok={status.r2Configured}
              />
              <StatusPill
                label={status.aiConfigured ? "AI ready" : "AI env missing"}
                ok={status.aiConfigured}
              />
              <StatusPill
                label={
                  status.databaseConfigured ? "Neon ready" : "Neon env missing"
                }
                ok={status.databaseConfigured}
              />
              <StatusPill
                label={
                  status.metadataStorage === "neon"
                    ? "Saving to Neon"
                    : "Saving local beta data"
                }
                ok
              />
            </div>
          </section>

          <section className="rounded-md border border-zinc-300 bg-white p-4 shadow-sm">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-zinc-800">
              <Database aria-hidden="true" className="h-4 w-4" />
              Recent entries
            </h2>
            {assets.length ? (
              <ul className="space-y-3">
                {assets.map((asset) => (
                  <li
                    className="rounded-md border border-zinc-200 bg-zinc-50 p-3"
                    key={asset.id}
                  >
                    <div className="font-medium">{asset.label}</div>
                    <div className="mt-1 text-sm text-zinc-600">
                      {[asset.hostname, asset.location, asset.assetTag]
                        .filter(Boolean)
                        .join(" / ") || "No location or asset tag"}
                    </div>
                    <div className="mt-2 text-xs text-zinc-500">
                      {asset.photoCount} photos / {asset.noteCount} notes
                    </div>
                    {asset.notes[0] ? (
                      <p className="mt-2 line-clamp-3 text-sm text-zinc-700">
                        {asset.notes[0]}
                      </p>
                    ) : null}
                    {asset.photos.length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {asset.photos.slice(0, 3).map((photo) => (
                          <div className="flex max-w-full flex-wrap gap-2" key={photo.key}>
                            <PhotoOpenButton
                              filename={photo.filename}
                              objectKey={photo.key}
                            />
                            <AnalyzePhotoButton
                              assetId={asset.id}
                              disabled={!status.aiConfigured}
                              filename={photo.filename}
                              objectKey={photo.key}
                            />
                          </div>
                        ))}
                      </div>
                    ) : null}
                    {asset.latestAnalysis?.result ? (
                      <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-950">
                        <div className="font-semibold">
                          {asset.latestAnalysis.result.primaryIdentification}
                        </div>
                        <div className="mt-1 text-xs uppercase tracking-[0.12em] text-emerald-800">
                          {asset.latestAnalysis.result.equipmentCategory} /{" "}
                          {asset.latestAnalysis.result.confidence} confidence
                        </div>
                        {asset.latestAnalysis.result.visibleText.length ? (
                          <div className="mt-2 text-xs text-emerald-900">
                            Text:{" "}
                            {asset.latestAnalysis.result.visibleText
                              .slice(0, 4)
                              .join(" / ")}
                          </div>
                        ) : null}
                        {asset.latestAnalysis.result.suggestedFollowUp[0] ? (
                          <div className="mt-2 text-xs text-emerald-900">
                            Next:{" "}
                            {asset.latestAnalysis.result.suggestedFollowUp[0]}
                          </div>
                        ) : null}
                      </div>
                    ) : asset.latestAnalysis?.error ? (
                      <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                        AI analysis failed: {asset.latestAnalysis.error}
                      </div>
                    ) : asset.latestAnalysis ? (
                      <div className="mt-3 rounded-md border border-sky-200 bg-sky-50 p-3 text-sm text-sky-900">
                        AI analysis {asset.latestAnalysis.status}. Worker will
                        process it shortly.
                      </div>
                    ) : null}
                    <div className="mt-3 flex items-center gap-1.5 text-xs font-medium uppercase tracking-[0.12em] text-zinc-500">
                      <HardDrive aria-hidden="true" className="h-3.5 w-3.5" />
                      {asset.storage}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-zinc-600">
                Recent entries will appear here after the first beta capture is
                saved.
              </p>
            )}
          </section>
        </aside>
      </div>
    </main>
  );
}
