import Stat from "@/components/ui/Stat";
import type { JobResult } from "@/types/catalog";

type StatsGridProps = {
  result: JobResult;
};

export default function StatsGrid({
  result,
}: StatsGridProps) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Stat
        label="Products"
        value={result.input_products}
      />

      <Stat
        label="Processed"
        value={result.processed}
      />

      <Stat
        label="Duplicates"
        value={result.duplicates}
      />

      <Stat
        label="Processing time"
        value={
          result.processing_time_seconds
            ? `${result.processing_time_seconds}s`
            : "-"
        }
      />
    </div>
  );
}