export type JobResult = {
  input_products?: number;
  unique_products?: number;
  duplicates?: number;
  processed?: number;
  cache_hits?: number;
  cache_misses?: number;
  processing_time_seconds?: number;
  validation_errors?: unknown[];
  filename?: string;
  job_id?: string;
};

export type ProcessResponse = {
  result: JobResult;
  download_url: string;
};

export type JobStatus = {
  job_id: string;

  status:
    | "queued"
    | "processing"
    | "completed"
    | "cancelled"
    | "failed";

  progress?: number;

  processed?: number;

  total?: number;

  message?: string;

  result?: JobResult;
};

export type CancelResponse = {
  success: boolean;
  job_id?: string;
  status: string;
  message: string;
};

export type ProcessedFile = {
  id: string;
  filename: string;
  products: number;
  processed: number;
  duplicates: number;
  processingTime: number;
  processedAt: string;
};