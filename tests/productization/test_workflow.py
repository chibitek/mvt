import pytest

from mvt.productization import (
    AlertReviewFilter,
    AnalysisRunRecord,
    ArtifactRecord,
    CaseIntakeRequest,
    ReviewerNoteRequest,
    TimelineReviewFilter,
    build_evidence_export_manifest,
    build_run_status_view,
)


CREATED_AT = "2026-05-28T00:00:00Z"


def test_case_intake_builds_linked_tenant_records():
    request = CaseIntakeRequest(
        tenant_id="tenant-1",
        title="Executive phone review",
        platform="ios",
        device_label="CEO iPhone",
        acquisition_type="ios_backup",
        source_uri="s3://tenant-1/acquisitions/acq-1",
        opened_by_profile_id="profile-1",
        owner_reference="exec-1",
        captured_at="2026-05-27T23:00:00Z",
        metadata={"custodian": "executive"},
    )

    case = request.to_case_record(case_id="case-1", created_at=CREATED_AT)
    device = request.to_device_record(
        device_id="device-1",
        case_id=case.id,
        created_at=CREATED_AT,
    )
    acquisition = request.to_acquisition_record(
        acquisition_id="acq-1",
        case_id=case.id,
        device_id=device.id,
        created_at=CREATED_AT,
    )

    assert case.tenant_id == "tenant-1"
    assert case.title == "Executive phone review"
    assert device.case_id == "case-1"
    assert device.platform == "ios"
    assert acquisition.device_id == "device-1"
    assert acquisition.source_uri == "s3://tenant-1/acquisitions/acq-1"


def test_case_intake_requires_source_uri():
    with pytest.raises(ValueError, match="source_uri is required"):
        CaseIntakeRequest(
            tenant_id="tenant-1",
            title="Executive phone review",
            platform="ios",
            device_label="CEO iPhone",
            acquisition_type="ios_backup",
            source_uri="",
        )


def test_run_status_view_uses_summary_alert_counts_and_camel_case():
    run = AnalysisRunRecord(
        id="run-1",
        tenant_id="tenant-1",
        case_id="case-1",
        acquisition_id="acq-1",
        status="completed",
        command=["mvt-ios", "check-backup"],
        mvt_version="2026.5.12",
        started_at="2026-05-28T00:00:00Z",
        completed_at="2026-05-28T00:01:00Z",
        summary={"alertCounts": {"HIGH": 2}},
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )

    view = build_run_status_view(run, artifact_count=4, timeline_count=20)
    data = view.to_dict()

    assert data["runId"] == "run-1"
    assert data["mvtVersion"] == "2026.5.12"
    assert data["alertCounts"] == {"HIGH": 2}
    assert data["artifactCount"] == 4
    assert data["timelineCount"] == 20


def test_review_filters_validate_tenant_and_limits():
    assert AlertReviewFilter(tenant_id="tenant-1", level="HIGH").limit == 100
    assert TimelineReviewFilter(tenant_id="tenant-1", run_id="run-1").limit == 200

    with pytest.raises(ValueError, match="tenant_id is required"):
        AlertReviewFilter(tenant_id="")
    with pytest.raises(ValueError, match="limit must be between 1 and 500"):
        TimelineReviewFilter(tenant_id="tenant-1", run_id="run-1", limit=501)


def test_reviewer_note_request_builds_record():
    request = ReviewerNoteRequest(
        tenant_id="tenant-1",
        case_id="case-1",
        run_id="run-1",
        alert_id="alert-1",
        author_profile_id="profile-1",
        body="Escalated to incident response.",
    )

    record = request.to_record(note_id="note-1", created_at=CREATED_AT)

    assert record.id == "note-1"
    assert record.tenant_id == "tenant-1"
    assert record.alert_id == "alert-1"
    assert record.visibility == "internal"


def test_evidence_export_manifest_prefers_storage_uri():
    artifacts = [
        ArtifactRecord(
            id="artifact-1",
            tenant_id="tenant-1",
            run_id="run-1",
            name="alerts.json",
            path="/runs/run-1/alerts.json",
            kind="alerts",
            size_bytes=128,
            sha256="abc",
            storage_uri="s3://tenant-1/runs/run-1/alerts.json",
            created_at=CREATED_AT,
            updated_at=CREATED_AT,
        )
    ]

    manifest = build_evidence_export_manifest(
        case_id="case-1",
        run_id="run-1",
        artifacts=artifacts,
        generated_at=CREATED_AT,
    )

    assert manifest.to_dict()["artifactPaths"] == [
        "s3://tenant-1/runs/run-1/alerts.json"
    ]
