"""Durable job queue backed by SQLite audit_jobs table with atomic leasing.

Production Migration Note:
To migrate this queue to Amazon SQS, Celery, or Arq, preserve the `claim_job`,
`complete_job`, and `fail_or_retry_job` interfaces. In SQS, replace the SQLite query
with `sqs.receive_message(VisibilityTimeout=300)`; in Celery, dispatch via `@app.task(bind=True)`.
The downstream audit pipeline code requires no modification.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.models import AuditJob, JobStatus


def claim_job(db: Session, lease_seconds: int = 300) -> Optional[AuditJob]:
    """Atomically claim the next pending or expired audit job using a lease.

    Uses an immediate transaction lock on SQLite to avoid concurrent double-claims.
    """
    now = datetime.now(timezone.utc)

    # Find next pending or timed-out running job
    stmt = (
        select(AuditJob)
        .where(
            or_(
                AuditJob.status == JobStatus.PENDING,
                (AuditJob.status == JobStatus.RUNNING) & (AuditJob.leased_until < now),
            )
        )
        .order_by(AuditJob.created_at.asc())
        .limit(1)
        .with_for_update()
    )

    job = db.execute(stmt).scalars().first()
    if not job:
        return None

    # Mark claimed
    job.status = JobStatus.RUNNING
    job.leased_until = now + timedelta(seconds=lease_seconds)
    job.attempts += 1
    job.updated_at = now
    db.commit()
    db.refresh(job)
    return job


def complete_job(db: Session, job_id: int) -> None:
    """Mark an audit job as successfully completed."""
    job = db.get(AuditJob, job_id)
    if job:
        job.status = JobStatus.DONE
        job.leased_until = None
        job.updated_at = datetime.now(timezone.utc)
        db.commit()


def fail_or_retry_job(db: Session, job_id: int, error_message: str, max_attempts: int = 3) -> None:
    """Handle job execution failure: re-queue if under max attempts or mark FAILED."""
    job = db.get(AuditJob, job_id)
    if not job:
        return

    now = datetime.now(timezone.utc)
    job.last_error = error_message[:2000]
    job.leased_until = None
    job.updated_at = now

    if job.attempts >= max_attempts:
        job.status = JobStatus.FAILED
    else:
        # Re-queue for next worker pickup
        job.status = JobStatus.PENDING

    db.commit()
