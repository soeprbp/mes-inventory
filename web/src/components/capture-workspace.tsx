import { logoutAction } from "@/app/actions";
import { AnalyzePhotoButton } from "@/components/analyze-photo-button";
import { CaptureForm } from "@/components/capture-form";
import { PhotoOpenButton } from "@/components/photo-open-button";
import type { AssetSummary } from "@/lib/assets";
import type { RuntimeStatus } from "@/lib/runtime-status";
import {
  Activity,
  Bot,
  Camera,
  CheckCircle2,
  Clock3,
  Database,
  HardDrive,
  LogOut,
  MapPin,
  Server,
  Tag,
  TriangleAlert,
} from "lucide-react";
import type { ElementType } from "react";

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

function Metric({
  icon: Icon,
  label,
  value,
}: {
  icon: ElementType;
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-md border border-zinc-200 bg-zinc-50 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-zinc-500">{label}</span>
        <Icon aria-hidden="true" className="h-4 w-4 text-zinc-500" />
      </div>
      <div className="mt-2 text-2xl font-semibold tabular-nums text-zinc-950">
        {value}
      </div>
    </div>
  );
}

function AnalysisBadge({ status }: { status?: string }) {
  if (!status) {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs font-medium text-zinc-500">
        <Clock3 aria-hidden="true" className="h-3.5 w-3.5" />
        no analysis
      </span>
    );
  }

  const isDone = status === "succeeded";
  const isFailed = status === "failed";

  return (
    <span
      className={[
        "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium",
        isDone
          ? "border-emerald-200 bg-emerald-50 text-emerald-800"
          : isFailed
            ? "border-red-200 bg-red-50 text-red-800"
            : "border-sky-200 bg-sky-50 text-sky-800",
      ].join(" ")}
    >
      {isDone ? (
        <CheckCircle2 aria-hidden="true" className="h-3.5 w-3.5" />
      ) : isFailed ? (
        <TriangleAlert aria-hidden="true" className="h-3.5 w-3.5" />
      ) : (
        <Activity aria-hidden="true" className="h-3.5 w-3.5" />
      )}
      {status}
    </span>
  );
}

export function CaptureWorkspace({ assets, status }: CaptureWorkspaceProps) {
  const photoTotal = assets.reduce((sum, asset) => sum + asset.photoCount, 0);
  const analyzedTotal = assets.filter(
    (asset) => asset.latestAnalysis?.status === "succeeded",
  ).length;
  const queuedTotal = assets.filter((asset) =>
    ["queued", "running"].includes(asset.latestAnalysis?.status ?? ""),
  ).length;

  return (
    <main className="min-h-dvh bg-[#eef2ef] text-zinc-950">
      <header className="sticky top-0 z-20 border-b border-zinc-300 bg-white/95 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-700">
              MES Inventory
            </p>
            <h1 className="text-xl font-semibold">Field capture beta</h1>
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
        <section className="rounded-md border border-zinc-300 bg-white shadow-sm">
          <div className="border-b border-zinc-200 p-4 sm:p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-zinc-950 text-white">
                <Camera aria-hidden="true" className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">New equipment entry</h2>
                <p className="text-sm text-zinc-600">
                  Capture enough context for maintenance, networking, and later
                  AI review.
                </p>
              </div>
            </div>
          </div>
          <div className="p-4 sm:p-5">
            <CaptureForm databaseConfigured={status.databaseConfigured} />
          </div>
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
              <Activity aria-hidden="true" className="h-4 w-4" />
              Field totals
            </h2>
            <div className="grid grid-cols-2 gap-2">
              <Metric icon={Database} label="Entries" value={assets.length} />
              <Metric icon={Camera} label="Photos" value={photoTotal} />
              <Metric icon={Bot} label="Analyzed" value={analyzedTotal} />
              <Metric icon={Clock3} label="Queued" value={queuedTotal} />
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
                    className="rounded-md border border-zinc-200 bg-white p-3 shadow-[0_1px_0_rgba(0,0,0,0.03)]"
                    key={asset.id}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate font-semibold text-zinc-950">
                          {asset.label}
                        </div>
                        <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-zinc-600">
                          {asset.location ? (
                            <span className="inline-flex items-center gap-1">
                              <MapPin
                                aria-hidden="true"
                                className="h-3.5 w-3.5"
                              />
                              {asset.location}
                            </span>
                          ) : null}
                          {asset.assetTag ? (
                            <span className="inline-flex items-center gap-1">
                              <Tag
                                aria-hidden="true"
                                className="h-3.5 w-3.5"
                              />
                              {asset.assetTag}
                            </span>
                          ) : null}
                        </div>
                      </div>
                      <AnalysisBadge status={asset.latestAnalysis?.status} />
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-zinc-500">
                      <span>{asset.photoCount} photos</span>
                      <span>{asset.noteCount} notes</span>
                      {asset.equipmentTypeGuess ? (
                        <span>{asset.equipmentTypeGuess}</span>
                      ) : null}
                    </div>
                    {asset.notes[0] ? (
                      <p className="mt-2 line-clamp-3 text-sm text-zinc-700">
                        {asset.notes[0]}
                      </p>
                    ) : null}
                    {asset.photos.length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {asset.photos.slice(0, 3).map((photo) => (
                          <div
                            className="flex max-w-full flex-wrap gap-2"
                            key={photo.key}
                          >
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
                        <div className="flex items-start gap-2">
                          <Bot aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-emerald-700" />
                          <div className="min-w-0">
                            <div className="font-semibold">
                              {asset.latestAnalysis.result.primaryIdentification}
                            </div>
                            <div className="mt-1 flex flex-wrap gap-1.5 text-xs">
                              <span className="rounded bg-white/70 px-1.5 py-0.5 font-medium text-emerald-800">
                                {asset.latestAnalysis.result.equipmentCategory}
                              </span>
                              <span className="rounded bg-white/70 px-1.5 py-0.5 font-medium text-emerald-800">
                                {asset.latestAnalysis.result.confidence}{" "}
                                confidence
                              </span>
                              {asset.latestAnalysis.result.manufacturer ? (
                                <span className="rounded bg-white/70 px-1.5 py-0.5 font-medium text-emerald-800">
                                  {asset.latestAnalysis.result.manufacturer}
                                </span>
                              ) : null}
                            </div>
                          </div>
                        </div>
                        {asset.latestAnalysis.result.visibleText.length ? (
                          <div className="mt-3 text-xs text-emerald-900">
                            <span className="font-semibold">Visible text:</span>{" "}
                            {asset.latestAnalysis.result.visibleText
                              .slice(0, 4)
                              .join(" / ")}
                          </div>
                        ) : null}
                        {asset.latestAnalysis.result.suggestedFollowUp[0] ? (
                          <div className="mt-2 text-xs text-emerald-900">
                            <span className="font-semibold">Next:</span>{" "}
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
