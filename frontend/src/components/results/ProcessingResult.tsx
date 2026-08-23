import {
  CheckCircle2,
  Download,
} from "lucide-react";

import StatsGrid from "@/components/dashboard/StatsGrid";
import type { JobResult } from "@/types/catalog";

type ProcessingResultProps = {
  result: JobResult;
  downloadUrl: string;
  onProcessAnother: () => void;
};

export default function ProcessingResult({
  result,
  downloadUrl,
  onProcessAnother,
}: ProcessingResultProps) {
  return (
    <div>
      <div className="mb-5 flex items-center gap-3">
        <CheckCircle2
          size={22}
          className="text-emerald-400"
        />

        <div>
          <div className="text-sm font-medium">
            Processing complete
          </div>

          <div className="text-xs text-zinc-500">
            {result.filename}
          </div>
        </div>
      </div>

      <StatsGrid result={result} />

      <div className="mt-5 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
        <div className="text-sm font-medium">
          Output ready
        </div>

        <div className="mt-1 text-xs text-zinc-500">
          Your enriched catalog has been generated.
        </div>

        {downloadUrl && (
          <a
            href={downloadUrl}
            className="mt-5 flex items-center justify-center gap-2 rounded-lg bg-zinc-100 px-4 py-3 text-sm font-medium text-zinc-950 hover:bg-white"
          >
            <Download size={17} />
            Download Excel
          </a>
        )}
      </div>

      <button
        onClick={onProcessAnother}
        className="mt-5 text-xs text-zinc-500 hover:text-zinc-300"
      >
        Process another file
      </button>
    </div>
  );
}