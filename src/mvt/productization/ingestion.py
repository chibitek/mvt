"""Convert normalized MVT summaries into storage records."""

from __future__ import annotations

from dataclasses import dataclass

from .artifacts import NormalizedRunSummary
from .models import AlertRecord, ArtifactRecord


@dataclass(frozen=True)
class RunIngestionRecords:
    artifacts: list[ArtifactRecord]
    alerts: list[AlertRecord]


def build_run_ingestion_records(
    summary: NormalizedRunSummary,
    *,
    tenant_id: str,
    run_id: str | None = None,
    created_at: str,
) -> RunIngestionRecords:
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not created_at:
        raise ValueError("created_at is required")

    storage_run_id = run_id or summary.run_id
    artifacts = [
        ArtifactRecord(
            id=f"{storage_run_id}:artifact:{index}",
            tenant_id=tenant_id,
            run_id=storage_run_id,
            name=artifact.name,
            path=artifact.path,
            kind=artifact.kind,
            size_bytes=artifact.size_bytes,
            sha256=artifact.sha256,
            created_at=created_at,
            updated_at=created_at,
        )
        for index, artifact in enumerate(summary.artifact_refs)
    ]
    alerts = [
        AlertRecord(
            id=f"{storage_run_id}:alert:{index}",
            tenant_id=tenant_id,
            run_id=storage_run_id,
            level=alert.level,
            module=alert.module,
            message=alert.message,
            event_time=alert.event_time,
            matched_indicator=alert.matched_indicator,
            created_at=created_at,
            updated_at=created_at,
        )
        for index, alert in enumerate(summary.alerts)
    ]
    return RunIngestionRecords(artifacts=artifacts, alerts=alerts)
