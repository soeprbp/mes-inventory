"use client";

import { Camera, CheckCircle2, LoaderCircle, Save, Upload } from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";

type UploadedPhoto = {
  key: string;
  filename: string;
  contentType: string;
  sizeBytes: number;
};

type CaptureFormProps = {
  databaseConfigured: boolean;
};

type SubmitState =
  | { kind: "idle" }
  | { kind: "saving"; message: string }
  | { kind: "success"; message: string }
  | { kind: "error"; message: string };

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const body = (await response.json()) as T & { error?: string };

  if (!response.ok) {
    throw new Error(body.error ?? "Request failed.");
  }

  return body;
}

export function CaptureForm({ databaseConfigured }: CaptureFormProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<SubmitState>({ kind: "idle" });
  const [fileCount, setFileCount] = useState(0);

  const statusClasses = useMemo(() => {
    if (state.kind === "error") {
      return "border-red-200 bg-red-50 text-red-800";
    }

    if (state.kind === "success") {
      return "border-emerald-200 bg-emerald-50 text-emerald-800";
    }

    return "border-zinc-200 bg-zinc-50 text-zinc-700";
  }, [state.kind]);

  async function uploadPhotos(files: File[]): Promise<UploadedPhoto[]> {
    const uploaded: UploadedPhoto[] = [];

    for (const file of files) {
      setState({ kind: "saving", message: `Uploading ${file.name}` });
      const signed = await parseJsonResponse<{
        key: string;
        uploadUrl: string;
      }>(
        await fetch("/api/upload-url", {
          body: JSON.stringify({
            filename: file.name,
            contentType: file.type || "image/jpeg",
            sizeBytes: file.size,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        }),
      );

      const uploadResponse = await fetch(signed.uploadUrl, {
        body: file,
        headers: { "content-type": file.type || "image/jpeg" },
        method: "PUT",
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed for ${file.name}.`);
      }

      uploaded.push({
        key: signed.key,
        filename: file.name,
        contentType: file.type || "image/jpeg",
        sizeBytes: file.size,
      });
    }

    return uploaded;
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const files = Array.from(fileRef.current?.files ?? []);
    const field = (name: string) => String(formData.get(name) ?? "");

    try {
      setState({ kind: "saving", message: "Preparing entry" });
      const photos = files.length ? await uploadPhotos(files) : [];

      setState({ kind: "saving", message: "Saving metadata" });
      await parseJsonResponse(
        await fetch("/api/assets", {
          body: JSON.stringify({
            label: field("label"),
            hostname: field("hostname"),
            location: field("location"),
            assetTag: field("assetTag"),
            manufacturer: field("manufacturer"),
            model: field("model"),
            serialNumber: field("serialNumber"),
            equipmentTypeGuess: field("equipmentTypeGuess"),
            note: field("note"),
            photos,
          }),
          headers: { "content-type": "application/json" },
          method: "POST",
        }),
      );

      setState({ kind: "success", message: "Entry saved." });
      formRef.current?.reset();
      setFileCount(0);
    } catch (error) {
      setState({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Entry could not be saved.",
      });
    }
  }

  return (
    <form className="space-y-5" onSubmit={onSubmit} ref={formRef}>
      {!databaseConfigured ? (
        <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Neon is not connected yet. This beta will save metadata to the local
          field-test store on this machine.
        </div>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block sm:col-span-2">
          <span className="mb-1.5 block text-sm font-medium text-zinc-800">
            Equipment label
          </span>
          <input
            className="h-11 w-full rounded-md border border-zinc-300 px-3 text-base outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200"
            name="label"
            placeholder="Line 3 PLC cabinet"
            required
          />
        </label>

        <TextField label="Hostname" name="hostname" placeholder="PLC-L3-02" />
        <TextField label="Asset tag" name="assetTag" placeholder="MES-1042" />
        <TextField label="Location" name="location" placeholder="Plant 1 / Line 3" />
        <TextField label="Type guess" name="equipmentTypeGuess" placeholder="PLC, HMI, workstation" />
        <TextField label="Manufacturer" name="manufacturer" placeholder="Allen-Bradley" />
        <TextField label="Model" name="model" placeholder="ControlLogix" />
        <TextField label="Serial number" name="serialNumber" placeholder="SN or service tag" />
      </div>

      <label className="block">
        <span className="mb-1.5 block text-sm font-medium text-zinc-800">
          Notes
        </span>
        <textarea
          className="min-h-28 w-full resize-y rounded-md border border-zinc-300 px-3 py-2 text-base outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200"
          name="note"
          placeholder="Network ports, cabinet labels, observed condition, follow-up work."
        />
      </label>

      <div className="rounded-md border border-dashed border-zinc-400 bg-zinc-50 p-4">
        <span className="flex items-center gap-2 text-sm font-medium text-zinc-800">
          <Camera aria-hidden="true" className="h-4 w-4" />
          Photos
        </span>
        <input
          accept="image/*"
          className="mt-3 block w-full text-sm text-zinc-700 file:mr-3 file:h-10 file:rounded-md file:border-0 file:bg-zinc-950 file:px-3 file:text-sm file:font-semibold file:text-white"
          multiple
          onChange={(event) => setFileCount(event.target.files?.length ?? 0)}
          ref={fileRef}
          type="file"
        />
        <span className="mt-3 flex items-center gap-2 text-xs text-zinc-600">
          <Upload aria-hidden="true" className="h-3.5 w-3.5" />
          {fileCount
            ? `${fileCount} selected`
            : "Take new photos or choose existing images"}
        </span>
      </div>

      {state.kind !== "idle" ? (
        <div className={`rounded-md border px-3 py-2 text-sm ${statusClasses}`}>
          {state.message}
        </div>
      ) : null}

      <button
        className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-emerald-700 px-4 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:bg-zinc-500 sm:w-auto"
        disabled={state.kind === "saving"}
        type="submit"
      >
        {state.kind === "saving" ? (
          <LoaderCircle aria-hidden="true" className="h-4 w-4 animate-spin" />
        ) : state.kind === "success" ? (
          <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
        ) : (
          <Save aria-hidden="true" className="h-4 w-4" />
        )}
        Save entry
      </button>
    </form>
  );
}

function TextField({
  label,
  name,
  placeholder,
}: {
  label: string;
  name: string;
  placeholder: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-zinc-800">
        {label}
      </span>
      <input
        className="h-11 w-full rounded-md border border-zinc-300 px-3 text-base outline-none transition focus:border-emerald-600 focus:ring-2 focus:ring-emerald-200"
        name={name}
        placeholder={placeholder}
      />
    </label>
  );
}
