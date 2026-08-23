type StatProps = {
  label: string;
  value?: string | number;
};

export default function Stat({
  label,
  value,
}: StatProps) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
      <div className="text-xs text-zinc-500">
        {label}
      </div>

      <div className="mt-2 text-xl font-semibold">
        {value ?? "-"}
      </div>
    </div>
  );
}