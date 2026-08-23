"use client";

import {
  Clock3,
  Sparkles,
} from "lucide-react";

type ProcessingEstimateProps = {
  file: File;
};

function formatTime(seconds: number) {
  if (seconds < 60) {
    return `~${seconds} sec`;
  }

  const minutes = Math.ceil(seconds / 60);

  return `~${minutes} min`;
}

export default function ProcessingEstimate({
  file,
}: ProcessingEstimateProps) {
  /*
   * Rough frontend estimate.
   *
   * The backend can later provide a much
   * more accurate estimate based on:
   *
   * - number of products
   * - cache hits
   * - web research
   * - Ollama processing
   */

  const fileSizeMB =
    file.size / 1024 / 1024;

  /*
   * Conservative estimate based on
   * catalog processing overhead.
   */

  const estimatedSeconds = Math.max(
    15,
    Math.round(
      20 + fileSizeMB * 35
    )
  );

  return (
    <div className="mt-4 rounded-lg border border-zinc-800 bg-zinc-950/60 p-4">

      <div className="flex items-start gap-3">

        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-zinc-900">
          <Clock3
            size={15}
            className="text-zinc-400"
          />
        </div>

        <div className="min-w-0 flex-1">

          <div className="flex items-center gap-2 text-xs font-medium text-zinc-300">
            Estimated processing time

            <Sparkles
              size={12}
              className="text-zinc-600"
            />
          </div>

          <div className="mt-1 text-sm text-zinc-400">
            {formatTime(estimatedSeconds)}
          </div>

          <div className="mt-1 text-[11px] leading-4 text-zinc-600">
            Estimate depends on catalog size,
            web research and AI enrichment.
          </div>

        </div>

      </div>

    </div>
  );
}