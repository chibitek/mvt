import pytest

from mvt.productization import CaseRecord, build_event, validate_tenant_record


def test_tenant_record_validation_requires_tenant_and_timestamps():
    record = CaseRecord(
        id="case-1",
        tenant_id="tenant-1",
        created_at="2026-05-28T00:00:00Z",
        updated_at="2026-05-28T00:00:00Z",
        title="Executive phone review",
    )

    validate_tenant_record(record)


def test_build_event_adds_tenant_scope_to_payload():
    event = build_event(
        "mvt.analysis.completed",
        tenant_id="tenant-1",
        payload={"runId": "run-1", "caseId": "case-1"},
    )

    data = event.to_dict()

    assert data["type"] == "mvt.analysis.completed"
    assert data["tenantId"] == "tenant-1"
    assert data["payload"]["tenantId"] == "tenant-1"
    assert data["occurredAt"]


def test_event_rejects_mismatched_payload_tenant():
    with pytest.raises(ValueError, match="payload tenant"):
        build_event(
            "mvt.alert.detected",
            tenant_id="tenant-1",
            payload={"tenantId": "tenant-2", "alertId": "alert-1"},
        )
