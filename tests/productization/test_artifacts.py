import json

from mvt.productization import normalize_results


def test_normalize_results_counts_artifacts_alerts_timeline_and_modules(tmp_path):
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
                },
                {
                    "level": "LOW",
                    "module": "settings",
                    "message": "risky setting",
                    "event_time": "",
                },
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / "timeline.csv").write_text(
        "timestamp,module,event,data\n2026-05-28T00:00:00Z,sms,message,hello\n",
        encoding="utf-8",
    )
    (tmp_path / "sms.json").write_text(
        json.dumps([{"id": 1}, {"id": 2}]), encoding="utf-8"
    )
    (tmp_path / "sms_detected.json").write_text(
        json.dumps([{"id": 1}]), encoding="utf-8"
    )
    (tmp_path / "command.log").write_text("ran", encoding="utf-8")

    summary = normalize_results(
        tmp_path,
        run_id="run-1",
        status="completed",
        command=["mvt-ios", "check-backup"],
    )

    assert summary.run_id == "run-1"
    assert summary.mvt_version == "2026.5.12"
    assert summary.alert_counts["HIGH"] == 1
    assert summary.alert_counts["LOW"] == 1
    assert summary.timeline_count == 1
    assert summary.module_result_count == 2
    assert {ref.kind for ref in summary.artifact_refs} >= {
        "alerts",
        "timeline",
        "module_results",
        "module_detections",
        "log",
    }
    service_summary = summary.to_dict()
    assert service_summary["runId"] == "run-1"
    assert service_summary["mvtVersion"] == "2026.5.12"
    assert service_summary["artifactRefs"][0]["sha256"]
