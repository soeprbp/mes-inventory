"use client";

import { Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

type AnalyzePhotoButtonProps = {
  assetId: string;
  disabled: boolean;
  filename: string;
  objectKey: string;
};

export function AnalyzePhotoButton({
  assetId,
  disabled,
  filename,
  objectKey,
}: AnalyzePhotoButtonProps) {
  const router = useRouter();
  const [state, setState] = useState<"idle" | "queueing" | "error">("idle");

  async function analyzePhoto() {
    setState("queueing");

    try {
      const response = await fetch("/api/analyze-photo", {
        body: JSON.stringify({ assetId, objectKey }),
        headers: { "content-type": "application/json" },
        method: "POST",
      });

      if (!response.ok) {
        const body = (await response.json()) as { error?: string };
        throw new Error(body.error ?? "Analysis failed.");
      }

      router.refresh();
      setState("idle");
    } catch {
      router.refresh();
      setState("error");
    }
  }

  return (
    <button
      className="inline-flex h-8 max-w-full items-center gap-1.5 rounded-md border border-emerald-300 bg-emerald-50 px-2 text-xs font-medium text-emerald-800 transition hover:bg-emerald-100 disabled:cursor-not-allowed disabled:border-zinc-300 disabled:bg-zinc-100 disabled:text-zinc-400"
      disabled={disabled || state === "queueing"}
      onClick={analyzePhoto}
      title={
        disabled
          ? "AI analysis is not configured"
          : `Analyze ${filename}`
      }
      type="button"
    >
      <Sparkles aria-hidden="true" className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate">
        {state === "queueing"
          ? "Queueing"
          : state === "error"
            ? "Retry"
            : "Analyze"}
      </span>
    </button>
  );
}
