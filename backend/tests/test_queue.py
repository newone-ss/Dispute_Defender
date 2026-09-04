"""Unit tests verifying durable SQLite queue leasing, crash recovery, and retries."""

from datetime import datetime, timedelta, timezone

from app.core.models import AuditJob, JobStatus
from app.core.queue import claim_job, complete_job, fail_or_retry_job


def test_queue_claim_and_complete(db_session):
    """Verify normal lease claiming and job completion."""
    job = AuditJob(dispute_id="disp_queue_01", status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()

    claimed = claim_job(db_session, lease_seconds=100)
    assert claimed is not None
    assert claimed.dispute_id == "disp_queue_01"
    assert claimed.status == JobStatus.RUNNING
    assert claimed.attempts == 1
    assert claimed.leased_until is not None

    complete_job(db_session, claimed.id)
    db_session.refresh(claimed)
    assert claimed.status == JobStatus.DONE


def test_queue_lease_expiration_recovery(db_session):
    """Verify timed-out running job is reclaimed by next worker (simulating crash)."""
    past_time = datetime.now(timezone.utc) - timedelta(seconds=60)
    crashed_job = AuditJob(
        dispute_id="disp_crash_01",
        status=JobStatus.RUNNING,
        attempts=1,
        leased_until=past_time,
    )
    db_session.add(crashed_job)
    db_session.commit()

    reclaimed = claim_job(db_session, lease_seconds=300)
    assert reclaimed is not None
    assert reclaimed.dispute_id == "disp_crash_01"
    assert reclaimed.status == JobStatus.RUNNING
    assert reclaimed.attempts == 2


def test_queue_retry_and_max_failures(db_session):
    """Verify job retry progression up to maximum failure threshold."""
    job = AuditJob(dispute_id="disp_retry_01", status=JobStatus.PENDING)
    db_session.add(job)
    db_session.commit()

    # Attempt 1: Fail -> Re-queue as PENDING
    claimed1 = claim_job(db_session)
    fail_or_retry_job(db_session, claimed1.id, "Transient Network Error", max_attempts=3)
    db_session.refresh(claimed1)
    assert claimed1.status == JobStatus.PENDING
    assert claimed1.attempts == 1

    # Attempt 2: Fail -> Re-queue as PENDING
    claimed2 = claim_job(db_session)
    fail_or_retry_job(db_session, claimed2.id, "Second Error", max_attempts=3)
    db_session.refresh(claimed2)
    assert claimed2.status == JobStatus.PENDING
    assert claimed2.attempts == 2

    # Attempt 3: Fail -> Mark FAILED
    claimed3 = claim_job(db_session)
    fail_or_retry_job(db_session, claimed3.id, "Final Terminal Error", max_attempts=3)
    db_session.refresh(claimed3)
    assert claimed3.status == JobStatus.FAILED
    assert claimed3.attempts == 3
    assert "Final Terminal Error" in claimed3.last_error
