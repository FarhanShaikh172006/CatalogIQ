import type {
  JobStatus,
  CancelResponse,
} from "@/types/catalog";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export async function startProcessing(
  file: File,
  signal?: AbortSignal
) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(
    `${API_URL}/api/process`,
    {
      method: "POST",
      body: formData,
      signal,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
        "Failed to start catalog processing."
    );
  }

  return data as {
    success: boolean;
    job_id: string;
    filename: string;
    status: string;
    progress: number;
  };
}


export async function getJobStatus(
  jobId: string,
  signal?: AbortSignal
): Promise<JobStatus> {

  const response = await fetch(
    `${API_URL}/api/status/${jobId}`,
    {
      method: "GET",
      signal,
      cache: "no-store",
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
        "Failed to get job status."
    );
  }

  return data;
}


export async function cancelJob(
  jobId: string
): Promise<CancelResponse> {

  const response = await fetch(
    `${API_URL}/api/cancel/${jobId}`,
    {
      method: "POST",
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
        "Failed to cancel processing."
    );
  }

  return data;
}


export function getDownloadUrl(
  jobId: string
): string {

  return `${API_URL}/api/download/${jobId}`;
}