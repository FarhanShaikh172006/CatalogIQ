from pathlib import Path
import time
import uuid
from threading import Event
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse

from app.pipeline.orchertrator import CatalogPipeline


router = APIRouter(
    prefix="/api",
    tags=["Catalog"],
)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path("data")

INPUT_DIR = BASE_DIR / "inputs"
OUTPUT_DIR = BASE_DIR / "outputs"

INPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# JOB STATE
# ============================================================

jobs: dict[str, dict[str, Any]] = {}


# ============================================================
# BASIC STATUS
# ============================================================

@router.get("/status")
def status():
    return {
        "status": "online",
        "service": "CatalogIQ",
    }


# ============================================================
# BACKGROUND JOB RUNNER
# ============================================================

def _run_catalog_job(
    job_id: str,
    input_path: Path,
    output_path: Path,
    filename: str,
    cancel_event: Event,
) -> None:

    job = jobs.get(job_id)

    if job is None:
        return

    try:
        # ----------------------------------------------------
        # Check cancellation before starting
        # ----------------------------------------------------

        if cancel_event.is_set():
            job["status"] = "cancelled"

            if input_path.exists():
                try:
                    input_path.unlink()
                except OSError:
                    pass

            return

        # ----------------------------------------------------
        # Mark job as processing
        # ----------------------------------------------------

        job["status"] = "processing"
        job["processing_started_at"] = time.perf_counter()

        # ----------------------------------------------------
        # Create pipeline WITH cancellation event
        # ----------------------------------------------------

        pipeline = CatalogPipeline(
            cancel_event=cancel_event,
        )

        # ----------------------------------------------------
        # Run pipeline
        # ----------------------------------------------------

        result = pipeline.process(
            input_path=input_path,
            output_path=output_path,
        )

        # ----------------------------------------------------
        # Check cancellation after pipeline
        # ----------------------------------------------------

        if cancel_event.is_set():

            job["status"] = "cancelled"

            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    pass

            return

        # ----------------------------------------------------
        # Processing time
        # ----------------------------------------------------

        elapsed = (
            time.perf_counter()
            - job["processing_started_at"]
        )

        result["processing_time_seconds"] = round(
            elapsed,
            2,
        )

        result["job_id"] = job_id
        result["filename"] = filename

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        job["result"] = result
        job["status"] = "completed"
        job["completed_at"] = time.perf_counter()

    except Exception as exc:

        # ----------------------------------------------------
        # Cancellation exception
        # ----------------------------------------------------

        if cancel_event.is_set():

            job["status"] = "cancelled"
            job["error"] = "Processing cancelled."

            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    pass

            return

        # ----------------------------------------------------
        # Actual processing failure
        # ----------------------------------------------------

        job["status"] = "failed"
        job["error"] = str(exc)

    finally:

        # ----------------------------------------------------
        # Remove uploaded input file
        # ----------------------------------------------------

        if input_path.exists():
            try:
                input_path.unlink()
            except OSError:
                pass


# ============================================================
# PROCESS CATALOG
# ============================================================

@router.post("/process")
async def process_catalog(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    # --------------------------------------------------------
    # Validate filename
    # --------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided.",
        )

    # --------------------------------------------------------
    # Validate extension
    # --------------------------------------------------------

    suffix = Path(file.filename).suffix.lower()

    if suffix not in {
        ".csv",
        ".xlsx",
        ".xls",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file format. "
                "Use CSV, XLSX, or XLS."
            ),
        )

    # --------------------------------------------------------
    # Create job ID
    # --------------------------------------------------------

    job_id = uuid.uuid4().hex

    input_path = (
        INPUT_DIR
        / f"{job_id}{suffix}"
    )

    output_path = (
        OUTPUT_DIR
        / f"{job_id}_CatalogIQ_Output.xlsx"
    )

    # --------------------------------------------------------
    # Create cancellation event
    # --------------------------------------------------------

    cancel_event = Event()

    jobs[job_id] = {
        "status": "queued",
        "filename": file.filename,
        "created_at": time.perf_counter(),
        "cancel_event": cancel_event,
        "input_path": input_path,
        "output_path": output_path,
    }

    # --------------------------------------------------------
    # Save uploaded file
    # --------------------------------------------------------

    try:

        content = await file.read()

        input_path.write_bytes(content)

    except Exception as exc:

        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(exc)

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save uploaded file: "
                f"{exc}"
            ),
        ) from exc

    # --------------------------------------------------------
    # Check cancellation before queueing
    # --------------------------------------------------------

    if cancel_event.is_set():

        jobs[job_id]["status"] = "cancelled"

        if input_path.exists():
            try:
                input_path.unlink()
            except OSError:
                pass

        return {
            "success": False,
            "cancelled": True,
            "job_id": job_id,
            "status": "cancelled",
            "message": "Processing cancelled.",
        }

    # --------------------------------------------------------
    # Queue background job
    # --------------------------------------------------------

    background_tasks.add_task(
        _run_catalog_job,
        job_id,
        input_path,
        output_path,
        file.filename,
        cancel_event,
    )

    # --------------------------------------------------------
    # Return immediately
    # --------------------------------------------------------

    return {
        "success": True,
        "job_id": job_id,
        "status": "queued",
        "message": "Catalog processing started.",
    }


# ============================================================
# CANCEL PROCESSING
# ============================================================

@router.post("/cancel/{job_id}")
def cancel_processing(
    job_id: str,
):
    job = jobs.get(job_id)

    # --------------------------------------------------------
    # Job doesn't exist
    # --------------------------------------------------------

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    status_value = job["status"]

    # --------------------------------------------------------
    # Already completed
    # --------------------------------------------------------

    if status_value == "completed":
        return {
            "success": False,
            "cancelled": False,
            "job_id": job_id,
            "status": "completed",
            "message": "Job already completed.",
        }

    # --------------------------------------------------------
    # Already cancelled
    # --------------------------------------------------------

    if status_value == "cancelled":
        return {
            "success": True,
            "cancelled": True,
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job already cancelled.",
        }

    # --------------------------------------------------------
    # Already failed
    # --------------------------------------------------------

    if status_value == "failed":
        return {
            "success": False,
            "cancelled": False,
            "job_id": job_id,
            "status": "failed",
            "message": "Job already failed.",
        }

    # --------------------------------------------------------
    # Signal cancellation
    # --------------------------------------------------------

    cancel_event: Event = job["cancel_event"]

    cancel_event.set()

    job["status"] = "cancelling"
    job["cancel_requested_at"] = time.perf_counter()

    # --------------------------------------------------------
    # Remove output if it somehow already exists
    # --------------------------------------------------------

    output_path = job.get("output_path")

    if isinstance(output_path, Path):
        if output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass

    return {
        "success": True,
        "cancelled": True,
        "job_id": job_id,
        "status": "cancelling",
        "message": "Cancellation requested.",
    }


# ============================================================
# JOB STATUS
# ============================================================

@router.get("/status/{job_id}")
def job_status(
    job_id: str,
):
    job = jobs.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    response = {
        "job_id": job_id,
        "status": job["status"],
        "filename": job.get("filename"),
        "error": job.get("error"),
    }

    # --------------------------------------------------------
    # Include result after completion
    # --------------------------------------------------------

    if job["status"] == "completed":
        response["result"] = job.get("result")

        response["download_url"] = (
            f"/api/download/{job_id}"
        )

    return response


# ============================================================
# DOWNLOAD RESULT
# ============================================================

@router.get("/download/{job_id}")
def download_result(
    job_id: str,
):
    job = jobs.get(job_id)

    # --------------------------------------------------------
    # Job doesn't exist
    # --------------------------------------------------------

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    # --------------------------------------------------------
    # Cancelled
    # --------------------------------------------------------

    if job["status"] in {
        "cancelled",
        "cancelling",
    }:
        raise HTTPException(
            status_code=410,
            detail=(
                "This processing job was cancelled."
            ),
        )

    # --------------------------------------------------------
    # Still processing
    # --------------------------------------------------------

    if job["status"] in {
        "queued",
        "processing",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Catalog is still being processed."
            ),
        )

    # --------------------------------------------------------
    # Failed
    # --------------------------------------------------------

    if job["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=(
                "Catalog processing failed: "
                f"{job.get('error', 'Unknown error')}"
            ),
        )

    # --------------------------------------------------------
    # Find output file
    # --------------------------------------------------------

    output_path = (
        OUTPUT_DIR
        / f"{job_id}_CatalogIQ_Output.xlsx"
    )

    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Output file not found.",
        )

    # --------------------------------------------------------
    # Return Excel file
    # --------------------------------------------------------

    return FileResponse(
        path=output_path,
        filename="CatalogIQ_Output.xlsx",
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )