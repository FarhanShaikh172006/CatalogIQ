"use client";

import { Loader2, Clock3, XCircle } from "lucide-react";

type ProcessingStatusProps = {
  filename?: string;
  estimatedSeconds?: number;
  onCancel?: () => void;
};

export default function ProcessingStatus({
  filename,
  estimatedSeconds,
  onCancel,
}: ProcessingStatusProps) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-8">
      {/* ICON */}
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-zinc-800">
        <Loader2
          size={22}
          className="animate-spin text-zinc-400"
        />
      </div>

      {/* TITLE */}
      <div className="mt-5 text-center">
        <div className="text-sm font-medium">
          Processing catalog
        </div>

        {filename && (
          <div className="mt-1 truncate text-xs text-zinc-500">
            {filename}
          </div>
        )}
      </div>

      {/* STATUS */}
      <div className="mt-6 flex items-center justify-center gap-2 text-xs text-zinc-500">
        <Clock3 size={13} />

        {estimatedSeconds ? (
          `Estimated time: ~${estimatedSeconds}s`
        ) : (
          "Researching products and generating enriched data..."
        )}
      </div>

      {/* PROCESSING INDICATOR */}
      <div className="mt-5 text-center text-xs text-zinc-600">
        This may take a few moments while products are researched,
        enriched and validated.
      </div>

      {/* CANCEL */}
      {onCancel && (
        <button
          type="button"
          onClick={onCancel}
          className="mx-auto mt-6 flex items-center justify-center gap-2 rounded-lg border border-zinc-700 px-5 py-2.5 text-sm text-zinc-400 transition hover:border-red-900/60 hover:bg-red-950/20 hover:text-red-300"
        >
          <XCircle size={16} />
          Cancel processing
        </button>
      )}
    </div>
  );
}
