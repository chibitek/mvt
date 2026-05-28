"""Workflow-facing DTOs for the Chibitek MVT SaaS surface."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .models import (
    AcquisitionRecord,
    AnalysisRunRecord,
    ArtifactRecord,
    CaseRecord,
    DeviceRecord,
    ReviewerNoteRecord,
)


@dataclass(frozen=True)
class CaseIntakeRequest:
    tenant_id: str
    title: str
    platform: str
    device_label: str
    acquisition_type: str
    source_uri: str
    opened_by_profile_id: str | None = None
    owner_reference: str | None = None
    captured_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text(self.tenant_id, "tenant_id")
        _require_text(self.title, "title")
        _require_text(self.platform, "platform")
        _require_text(self.device_label, "device_label")
        _require_text(self.acquisition_type, "acquisition_type")
        _require_text(self.source_uri, "source_uri")

    def to_case_record(self, *, case_id: str, created_at: str) -> CaseRecord:
        _require_text(case_id, "case_id")
        _require_text(created_at, "created_at")
        return CaseRecord(
            id=case_id,
            tenant_id=self.tenant_id,
            title=self.title,
            opened_by_profile_id=self.opened_by_profile_id,
            metadata=self.metadata,
            created_at=created_at,
            updated_at=created_at,
        )

    def to_device_record(
        self,
        *,
        device_id: str,
        case_id: str,
        created_at: str,
    ) -> DeviceRecord:
        _require_text(device_id, "device_id")
        _require_text(case_id, "case_id")
        _require_text(created_at, "created_at")
        return DeviceRecord(
            id=device_id,
            tenant_id=self.tenant_id,
            case_id=case_id,
            platform=self.platform,
            label=self.device_label,
            owner_reference=self.owner_reference,
            metadata=self.metadata,
            created_at=created_at,
            updated_at=created_at,
        )

    def to_acquisition_record(
        self,
        *,
        acquisition_id: str,
        case_id: str,
        device_id: str,
        created_at: str,
    ) -> AcquisitionRecord:
        _require_text(acquisition_id, "acquisition_id")
        _require_text(case_id, "case_id")
        _require_text(device_id, "device_id")
        _require_text(created_at, "created_at")
        return AcquisitionRecord(
            id=acquisition_id,
            tenant_id=self.tenant_id,
            case_id=case_id,
            device_id=device_id,
            acquisition_type=self.acquisition_type,
            source_uri=self.source_uri,
            captured_at=self.captured_at,
            metadata=self.metadata,
            created_at=created_at,
            updated_at=created_at,
        )


@dataclass(frozen=True)
class RunStatusView:
    run_id: str
    case_id: str
    acquisition_id: str
    status: str
    command: list[str]
    mvt_version: str | None
    started_at: str | None
    completed_at: str | None
    alert_counts: dict[str, int]
    artifact_count: int
    timeline_count: int
    error: str | None = None

    @classmethod
    def from_run(
        cls,
        run: AnalysisRunRecord,
        *,
        artifact_count: int = 0,
        timeline_count: int = 0,
        alert_counts: dict[str, int] | None = None,
    ) -> RunStatusView:
        return cls(
            run_id=run.id,
            case_id=run.case_id,
            acquisition_id=run.acquisition_id,
            status=run.status,
            command=list(run.command),
            mvt_version=run.mvt_version,
            started_at=run.started_at,
            completed_at=run.completed_at,
            alert_counts=alert_counts or _summary_alert_counts(run),
            artifact_count=artifact_count,
            timeline_count=timeline_count,
            error=run.error,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "runId": self.run_id,
            "caseId": self.case_id,
            "acquisitionId": self.acquisition_id,
            "status": self.status,
            "command": self.command,
            "mvtVersion": self.mvt_version,
            "startedAt": self.started_at,
            "completedAt": self.completed_at,
            "alertCounts": self.alert_counts,
            "artifactCount": self.artifact_count,
            "timelineCount": self.timeline_count,
            "error": self.error,
        }


@dataclass(frozen=True)
class AlertReviewFilter:
    tenant_id: str
    case_id: str | None = None
    run_id: str | None = None
    level: str | None = None
    module: str | None = None
    limit: int = 100

    def __post_init__(self) -> None:
        _require_text(self.tenant_id, "tenant_id")
        _validate_limit(self.limit, maximum=200)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimelineReviewFilter:
    tenant_id: str
    run_id: str
    module: str | None = None
    query: str | None = None
    limit: int = 200

    def __post_init__(self) -> None:
        _require_text(self.tenant_id, "tenant_id")
        _require_text(self.run_id, "run_id")
        _validate_limit(self.limit, maximum=500)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewerNoteRequest:
    tenant_id: str
    case_id: str
    body: str
    run_id: str | None = None
    alert_id: str | None = None
    author_profile_id: str | None = None
    visibility: str = "internal"

    def __post_init__(self) -> None:
        _require_text(self.tenant_id, "tenant_id")
        _require_text(self.case_id, "case_id")
        _require_text(self.body, "body")

    def to_record(self, *, note_id: str, created_at: str) -> ReviewerNoteRecord:
        _require_text(note_id, "note_id")
        _require_text(created_at, "created_at")
        return ReviewerNoteRecord(
            id=note_id,
            tenant_id=self.tenant_id,
            case_id=self.case_id,
            run_id=self.run_id,
            alert_id=self.alert_id,
            author_profile_id=self.author_profile_id,
            body=self.body,
            visibility=self.visibility,
            created_at=created_at,
            updated_at=created_at,
        )


@dataclass(frozen=True)
class EvidenceExportManifest:
    case_id: str
    run_id: str
    artifact_paths: list[str]
    generated_at: str
    include_alerts: bool = True
    include_timeline: bool = True

    def __post_init__(self) -> None:
        _require_text(self.case_id, "case_id")
        _require_text(self.run_id, "run_id")
        _require_text(self.generated_at, "generated_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "caseId": self.case_id,
            "runId": self.run_id,
            "artifactPaths": self.artifact_paths,
            "generatedAt": self.generated_at,
            "includeAlerts": self.include_alerts,
            "includeTimeline": self.include_timeline,
        }


def build_run_status_view(
    run: AnalysisRunRecord,
    *,
    artifact_count: int = 0,
    timeline_count: int = 0,
    alert_counts: dict[str, int] | None = None,
) -> RunStatusView:
    return RunStatusView.from_run(
        run,
        artifact_count=artifact_count,
        timeline_count=timeline_count,
        alert_counts=alert_counts,
    )


def build_evidence_export_manifest(
    *,
    case_id: str,
    run_id: str,
    artifacts: list[ArtifactRecord],
    generated_at: str,
    include_alerts: bool = True,
    include_timeline: bool = True,
) -> EvidenceExportManifest:
    return EvidenceExportManifest(
        case_id=case_id,
        run_id=run_id,
        artifact_paths=[artifact.storage_uri or artifact.path for artifact in artifacts],
        generated_at=generated_at,
        include_alerts=include_alerts,
        include_timeline=include_timeline,
    )


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} is required")


def _validate_limit(limit: int, *, maximum: int) -> None:
    if limit < 1 or limit > maximum:
        raise ValueError(f"limit must be between 1 and {maximum}")


def _summary_alert_counts(run: AnalysisRunRecord) -> dict[str, int]:
    alert_counts = run.summary.get("alertCounts") or run.summary.get("alert_counts") or {}
    return {str(key): int(value) for key, value in alert_counts.items()}
