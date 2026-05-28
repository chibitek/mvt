import json

from mvt.productization import build_run_ingestion_records, normalize_results


def test_build_run_ingestion_records_from_summary(tmp_path):
    (tmp_path / "info.json").write_text(
        json.dumps({"mvt_version": "2026.5.12"}), encoding="utf-8"
    )
    (tmp_path / "alerts.json").write_text(
        json.dumps(
            [
                {
                    "level": "HIGH",
                    "module": "sms",
                    "message": "matched sms",
                    "event_time": "2026-05-28T00:00:00Z",
                    "matched_indicator": {"value": "example.com"},
                }
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "sms.json").write_text(json.dumps([{"id": 1}]), encoding="utf-8")

    summary = normalize_results(
        tmp_path,
        run_id="run-1",
        status="completed",
        command=["mvt-ios", "check-backup"],
    )

    records = build_run_ingestion_records(
        summary,
        tenant_id="tenant-1",
        created_at="2026-05-28T00:00:00Z",
    )

    assert len(records.artifacts) == 3
    assert records.artifacts[0].tenant_id == "tenant-1"
    assert records.artifacts[0].run_id == "run-1"
    assert records.alerts[0].level == "HIGH"
    assert records.alerts[0].matched_indicator == {"value": "example.com"}
