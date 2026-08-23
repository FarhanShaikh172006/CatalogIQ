from dataclasses import dataclass, field
from threading import Event
from typing import Any


@dataclass
class Job:
    job_id: str
    filename: str

    cancel_event: Event = field(
        default_factory=Event
    )

    status: str = "processing"

    result: dict[str, Any] | None = None

    error: str | None = None


class JobManager:
    def __init__(self) -> None:
        self.jobs: dict[str, Job] = {}

    def create(
        self,
        job_id: str,
        filename: str,
    ) -> Job:

        job = Job(
            job_id=job_id,
            filename=filename,
        )

        self.jobs[job_id] = job

        return job

    def get(
        self,
        job_id: str,
    ) -> Job | None:

        return self.jobs.get(job_id)

    def cancel(
        self,
        job_id: str,
    ) -> bool:

        job = self.get(job_id)

        if job is None:
            return False

        if job.status in {
            "completed",
            "failed",
            "cancelled",
        }:
            return False

        job.cancel_event.set()

        job.status = "cancelling"

        return True


job_manager = JobManager()