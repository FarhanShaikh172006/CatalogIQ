"use client";

import {
  FileSpreadsheet,
  X,
} from "lucide-react";

import ProcessingEstimate from "./ProcessingEstimate";

type SelectedFileProps = {
  file: File;
  onRemove: () => void;
  onProcess: () => void;
};

export default function SelectedFile({
  file,
  onRemove,
  onProcess,
}: SelectedFileProps) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">

      {/* FILE */}

      <div className="flex items-center justify-between">

        <div className="flex min-w-0 items-center gap-4">

          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-zinc-800">
            <FileSpreadsheet
              size={19}
              className="text-zinc-300"
            />
          </div>

          <div className="min-w-0">

            <div className="truncate text-sm font-medium text-zinc-200">
              {file.name}
            </div>

            <div className="mt-1 text-xs text-zinc-500">
              {(file.size / 1024 / 1024).toFixed(2)} MB
            </div>

          </div>

        </div>

        <button
          type="button"
          onClick={onRemove}
          aria-label="Remove selected file"
          className="rounded-lg p-2 text-zinc-500 transition hover:bg-zinc-800 hover:text-zinc-200"
        >
          <X size={18} />
        </button>

      </div>

      {/* ESTIMATE */}

      <ProcessingEstimate
        file={file}
      />

      {/* PROCESS */}

      <button
        type="button"
        onClick={onProcess}
        className="mt-4 flex w-full items-center justify-center rounded-lg bg-zinc-100 px-4 py-3 text-sm font-medium text-zinc-950 transition hover:bg-white active:bg-zinc-200"
      >
        Process Catalog
      </button>

    </div>
  );
}