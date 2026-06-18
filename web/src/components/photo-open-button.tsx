"use client";

import { ImageIcon } from "lucide-react";
import { useState } from "react";

type PhotoOpenButtonProps = {
  filename: string;
  objectKey: string;
};

export function PhotoOpenButton({ filename, objectKey }: PhotoOpenButtonProps) {
  const [opening, setOpening] = useState(false);

  async function openPhoto() {
    setOpening(true);

    try {
      const response = await fetch("/api/photo-url", {
        body: JSON.stringify({ key: objectKey }),
        headers: { "content-type": "application/json" },
        method: "POST",
      });
      const body = (await response.json()) as { url?: string; error?: string };

      if (!response.ok || !body.url) {
        throw new Error(body.error ?? "Could not open photo.");
      }

      window.open(body.url, "_blank", "noopener,noreferrer");
    } finally {
      setOpening(false);
    }
  }

  return (
    <button
      className="inline-flex h-8 max-w-full items-center gap-1.5 rounded-md border border-zinc-300 bg-white px-2 text-xs font-medium text-zinc-700 transition hover:bg-zinc-100 disabled:cursor-wait disabled:text-zinc-400"
      disabled={opening}
      onClick={openPhoto}
      title={`Open ${filename}`}
      type="button"
    >
      <ImageIcon aria-hidden="true" className="h-3.5 w-3.5 shrink-0" />
      <span className="truncate">{opening ? "Opening" : filename}</span>
    </button>
  );
}
