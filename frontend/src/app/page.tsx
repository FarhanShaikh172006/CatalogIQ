
"use client";

import { useState } from "react";

import FileUpload from "@/components/upload/FileUpload";
import SelectedFile from "@/components/upload/SelectedFile";
import ProcessingStatus from "@/components/upload/ProcessingStatus";
import ProcessingResult from "@/components/results/ProcessingResult";
import Sidebar from "@/components/dashboard/Sidebar";

import {
  startProcessing,
  getJobStatus,
  cancelJob,
  getDownloadUrl,
} from "@/services/api";

import type {
  JobResult,
  ProcessedFile,
} from "@/types/catalog";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);

  const [processing, setProcessing] = useState(false);

  const [result, setResult] =
    useState<JobResult | null>(null);

  const [downloadUrl, setDownloadUrl] =
    useState("");

  const [error, setError] = useState("");

  const [processedFiles, setProcessedFiles] =
    useState<ProcessedFile[]>([]);

  const [jobId, setJobId] =
    useState<string | null>(null);

  const [abortController, setAbortController] =
    useState<AbortController | null>(null);

  // =========================================================
  // PROCESS CATALOG
  // =========================================================

  async function handleProcess() {
    if (!file) return;

    setProcessing(true);
    setResult(null);
    setDownloadUrl("");
    setError("");
    setJobId(null);

    const controller = new AbortController();

    setAbortController(controller);

    const startedAt = Date.now();

    try {
      // -----------------------------------------------------
      // Start backend job
      // -----------------------------------------------------

      const started = await startProcessing(
        file,
        controller.signal
      );

      const currentJobId = started.job_id;

      setJobId(currentJobId);

      // -----------------------------------------------------
      // Poll backend for status
      // -----------------------------------------------------

      while (true) {
        if (controller.signal.aborted) {
          return;
        }

        const status = await getJobStatus(
          currentJobId,
          controller.signal
        );

        // ---------------------------------------------------
        // Completed
        // ---------------------------------------------------

        if (status.status === "completed") {
          const processingTime =
            status.result?.processing_time_seconds ??
            Math.round(
              (Date.now() - startedAt) / 1000
            );

          if (status.result) {
            setResult(status.result);
          }

          setDownloadUrl(
            getDownloadUrl(currentJobId)
          );

          const processedFile: ProcessedFile = {
            id: `${Date.now()}-${file.name}`,

            filename: file.name,

            products:
              status.result?.processed ??
              status.result?.input_products ??
              0,

            processed:
              status.result?.processed ?? 0,

            duplicates:
              status.result?.duplicates ?? 0,

            processingTime,

            processedAt:
              new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              }),
          };

          setProcessedFiles((previous) => [
            processedFile,
            ...previous,
          ]);

          break;
        }

        // ---------------------------------------------------
        // Cancelled
        // ---------------------------------------------------

        if (status.status === "cancelled") {
          setError(
            "Processing was cancelled."
          );

          break;
        }

        // ---------------------------------------------------
        // Failed
        // ---------------------------------------------------

        if (status.status === "failed") {
          throw new Error(
            status.message ||
              "Catalog processing failed."
          );
        }

        // ---------------------------------------------------
        // Continue polling
        // ---------------------------------------------------

        await new Promise<void>((resolve) => {
          setTimeout(resolve, 1000);
        });
      }
    } catch (err) {
      // -----------------------------------------------------
      // AbortController cancellation
      // -----------------------------------------------------

      if (
        err instanceof DOMException &&
        err.name === "AbortError"
      ) {
        return;
      }

      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong."
      );
    } finally {
      setProcessing(false);
      setAbortController(null);
      setJobId(null);
    }
  }

  // =========================================================
  // CANCEL PROCESSING
  // =========================================================

  async function cancelProcessing() {
    const currentJobId = jobId;

    // Stop frontend polling
    abortController?.abort();

    // Tell backend to cancel the actual job
    if (currentJobId) {
      try {
        await cancelJob(currentJobId);
      } catch (err) {
        console.error(
          "Backend cancellation failed:",
          err
        );
      }
    }

    setProcessing(false);
    setResult(null);
    setDownloadUrl("");

    setError(
      "Processing cancelled."
    );

    setJobId(null);
    setAbortController(null);
  }

  // =========================================================
  // RESET
  // =========================================================

  function reset() {
    const currentJobId = jobId;

    // Tell backend to cancel if something is
    // still running.
    if (currentJobId) {
      cancelJob(currentJobId).catch((err) => {
        console.error(
          "Cancellation failed:",
          err
        );
      });
    }

    // Stop frontend polling
    abortController?.abort();

    setFile(null);
    setResult(null);
    setDownloadUrl("");
    setError("");
    setProcessing(false);
    setJobId(null);
    setAbortController(null);
  }

  // =========================================================
  // UI
  // =========================================================

  return (
    <main className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="flex min-h-screen">

        {/* =================================================
            SIDEBAR
        ================================================= */}

        <Sidebar
          processedFiles={processedFiles}
        />

        {/* =================================================
            MAIN CONTENT
        ================================================= */}

        <section className="min-w-0 flex-1">
          <div className="mx-auto max-w-5xl px-6 py-10 md:px-10">

            {/* =================================================
                HEADER
            ================================================= */}

            <div className="mb-10">
              <div className="text-sm text-zinc-500">
                Catalog processing
              </div>

              <h1 className="mt-2 text-3xl font-semibold tracking-tight">
                Enrich your product catalog
              </h1>

              <p className="mt-2 max-w-xl text-sm leading-6 text-zinc-500">
                Research, enrich, validate and
                export your product catalog
                using automated web research
                and AI enrichment.
              </p>
            </div>

            {/* =================================================
                UPLOAD
            ================================================= */}

            {!file &&
              !processing &&
              !result && (
                <FileUpload
                  onFileSelected={setFile}
                />
              )}

            {/* =================================================
                SELECTED FILE
            ================================================= */}

            {file &&
              !processing &&
              !result && (
                <SelectedFile
                  file={file}
                  onRemove={reset}
                  onProcess={handleProcess}
                />
              )}

            {/* =================================================
                PROCESSING
            ================================================= */}

            {processing && (
              <ProcessingStatus
                filename={file?.name}
                onCancel={cancelProcessing}
              />
            )}

            {/* =================================================
                ERROR
            ================================================= */}

            {error && !processing && (
              <div className="mt-5 rounded-xl border border-red-900/50 bg-red-950/20 p-4 text-sm text-red-300">
                <div className="font-medium">
                  Processing status
                </div>

                <div className="mt-1 text-red-400/80">
                  {error}
                </div>
              </div>
            )}

            {/* =================================================
                RESULT
            ================================================= */}

            {result && (
              <ProcessingResult
                result={result}
                downloadUrl={downloadUrl}
                onProcessAnother={reset}
              />
            )}

          </div>
        </section>
      </div>
    </main>
  );
}
