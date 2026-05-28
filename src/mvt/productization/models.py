"""Domain records for the Chibitek MVT SaaS wrapper."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

EVENT_TYPES = {
    "mvt.case.created",
    "mvt.analysis.started",
    "mvt.analysis.completed",
    "mvt.alert.detected",
    "mvt.followup.created",
}


@dataclass(frozen=True)
class TenantRecord:
    id: str
    tenant_id: str
    created_at: str
    updated_at: str
    deleted_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CaseRecord(TenantRecord):
    title: str = ""
    status: str = "open"
    opened_by_profile_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DeviceRecord(TenantRecord):
    case_id: str = ""
    platform: str = ""
    label: str = ""
    owner_reference: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AcquisitionRecord(TenantRecord):
    case_id: str = ""
    device_id: str = ""
    acquisition_type: str = ""
    source_uri: str = ""
    captured_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AnalysisRunRecord(TenantRecord):
    case_id: str = ""
    acquisition_id: str = ""
    status: str = "queued"
    command: list[str] = field(default_factory=list)
    mvt_version: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArtifactRecord(TenantRecord):
    run_id: str = ""
    name: str = ""
    path: str = ""
    kind: str = ""
    size_bytes: int = 0
    sha256: str = ""
    storage_uri: str | None = None


@dataclass(frozen=True)
class AlertRecord(TenantRecord):
    run_id: str = ""
    level: str = ""
    module: str = ""
    message: str = ""
    event_time: str = ""
    matched_indicator: Any = None


@dataclass(frozen=True)
class TimelineEventRecord(TenantRecord):
    run_id: str = ""
    timestamp: str = ""
    module: str = ""
    event: str = ""
    data: str = ""


@dataclass(frozen=True)
class ReviewerNoteRecord(TenantRecord):
    case_id: str = ""
    run_id: str | None = None
    alert_id: str | None = None
    author_profile_id: str | None = None
    body: str = ""
    visibility: str = "internal"


@dataclass(frozen=True)
class EventEnvelope:
    type: str
    tenant_id: str
    payload: dict[str, Any]
    id: str | None = None
    occurred_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        if self.type not in EVENT_TYPES:
            supported = ", ".join(sorted(EVENT_TYPES))
            raise ValueError(f"Unsupported event type {self.type!r}: {supported}")
        if not self.tenant_id:
            raise ValueError("tenant_id is required")
        payload_tenant_id = self.payload.get("tenantId") or self.payload.get("tenant_id")
        if payload_tenant_id and payload_tenant_id != self.tenant_id:
            raise ValueError("payload tenant does not match envelope tenant")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tenantId"] = data.pop("tenant_id")
        data["occurredAt"] = data.pop("occurred_at")
        return data


def build_event(
    event_type: str,
    *,
    tenant_id: str,
    payload: dict[str, Any],
    event_id: str | None = None,
) -> EventEnvelope:
    scoped_payload = dict(payload)
    scoped_payload.setdefault("tenantId", tenant_id)
    return EventEnvelope(
        id=event_id,
        type=event_type,
        tenant_id=tenant_id,
        payload=scoped_payload,
    )


def validate_tenant_record(record: TenantRecord) -> None:
    if not record.id:
        raise ValueError("id is required")
    if not record.tenant_id:
        raise ValueError("tenant_id is required")
    if not record.created_at:
        raise ValueError("created_at is required")
    if not record.updated_at:
        raise ValueError("updated_at is required")
