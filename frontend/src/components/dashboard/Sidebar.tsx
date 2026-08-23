"use client";

import {
  FileSpreadsheet,
  Clock3,
  CheckCircle2,
} from "lucide-react";

type ProcessedFile = {
  id: string;
  filename: string;
  products: number;
  processingTime?: number;
  processedAt: string;
};

type SidebarProps = {
  processedFiles: ProcessedFile[];
};

export default function Sidebar({
  processedFiles,
}: SidebarProps) {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-zinc-800 bg-[#0c0c0f] md:block">

      <div className="sticky top-0 flex h-screen flex-col p-5">

        {/* BRAND */}

        <div className="mb-10">
          <div className="text-xl font-semibold tracking-tight">
            CatalogIQ
          </div>

          <div className="mt-1 text-xs text-zinc-500">
            Intelligent catalog enrichment
          </div>
        </div>

        {/* PROCESSED FILES */}

        <div className="min-h-0 flex-1">

          <div className="mb-3 flex items-center justify-between">
            <div className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Processed Files
            </div>

            {processedFiles.length > 0 && (
              <div className="text-xs text-zinc-600">
                {processedFiles.length}
              </div>
            )}
          </div>

          {processedFiles.length === 0 ? (
            <div className="rounded-lg border border-zinc-800/70 bg-zinc-900/30 p-3">
              <div className="text-xs leading-5 text-zinc-600">
                Processed catalogs will appear here.
              </div>
            </div>
          ) : (
            <div className="space-y-2 overflow-y-auto">

              {processedFiles.map((item) => (
                <div
                  key={item.id}
                  className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3"
                >

                  <div className="flex items-start gap-3">

                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-zinc-800">
                      <FileSpreadsheet
                        size={15}
                        className="text-zinc-400"
                      />
                    </div>

                    <div className="min-w-0 flex-1">

                      <div className="truncate text-xs font-medium text-zinc-300">
                        {item.filename}
                      </div>

                      <div className="mt-1 flex items-center gap-2 text-[11px] text-zinc-600">
                        <span>
                          {item.products} products
                        </span>

                        <span>•</span>

                        <span>
                          {item.processedAt}
                        </span>
                      </div>

                    </div>

                  </div>

                  <div className="mt-3 flex items-center gap-2 border-t border-zinc-800 pt-2">

                    <CheckCircle2
                      size={12}
                      className="text-emerald-500"
                    />

                    <span className="text-[11px] text-zinc-600">
                      Completed
                    </span>

                    {item.processingTime !== undefined && (
                      <>
                        <span className="text-zinc-800">
                          •
                        </span>

                        <Clock3
                          size={11}
                          className="text-zinc-600"
                        />

                        <span className="text-[11px] text-zinc-600">
                          {item.processingTime}s
                        </span>
                      </>
                    )}

                  </div>

                </div>
              ))}

            </div>
          )}

        </div>

        {/* FOOTER */}

        <div className="border-t border-zinc-800 pt-4">
          <div className="text-[11px] text-zinc-600">
            CatalogIQ
          </div>

          <div className="mt-1 text-[11px] text-zinc-700">
            Automated catalog enrichment
          </div>
        </div>

      </div>
    </aside>
  );
}