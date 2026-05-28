"""Productization helpers for wrapping MVT in managed workflows."""

from .artifacts import (
    ArtifactRef,
    NormalizedAlert,
    NormalizedRunSummary,
    normalize_results,
)
from .ingestion import RunIngestionRecords, build_run_ingestion_records
from .models import (
    AcquisitionRecord,
    AlertRecord,
    AnalysisRunRecord,
    ArtifactRecord,
    CaseRecord,
    DeviceRecord,
    EventEnvelope,
    ReviewerNoteRecord,
    TimelineEventRecord,
    build_event,
    validate_tenant_record,
)
from .runner import MVTProductizationRunner, RunnerInput, RunnerOptions
from .schema import PRODUCTIZATION_TABLES, SCHEMA_SQL, validate_schema_contract

__all__ = [
    "AcquisitionRecord",
    "AlertRecord",
    "AnalysisRunRecord",
    "ArtifactRef",
    "ArtifactRecord",
    "CaseRecord",
    "DeviceRecord",
    "EventEnvelope",
    "MVTProductizationRunner",
    "NormalizedAlert",
    "NormalizedRunSummary",
    "PRODUCTIZATION_TABLES",
    "ReviewerNoteRecord",
    "RunIngestionRecords",
    "RunnerInput",
    "RunnerOptions",
    "SCHEMA_SQL",
    "TimelineEventRecord",
    "build_event",
    "build_run_ingestion_records",
    "normalize_results",
    "validate_schema_contract",
    "validate_tenant_record",
]
