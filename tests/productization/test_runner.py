import os
import stat

from mvt.productization import MVTProductizationRunner, RunnerInput, RunnerOptions


def test_build_command_maps_runner_contract_to_mvt_cli(tmp_path):
    runner_input = RunnerInput(
        case_id="case-1",
        acquisition_id="acq-1",
        platform="android",
        command="android_intrusion_logs",
        target_path=tmp_path / "logs",
        results_path=tmp_path / "out",
        ioc_files=[tmp_path / "indicators.stix2"],
        options=RunnerOptions(timezone="America/New_York", verbose=True),
    )

    command = MVTProductizationRunner().build_command(runner_input)

    assert command == [
        "mvt-android",
        "--disable-update-check",
        "--disable-indicator-update-check",
        "check-intrusion-logs",
        "--iocs",
        str(tmp_path / "indicators.stix2"),
        "--output",
        str(tmp_path / "out"),
        "--verbose",
        "--timezone",
        "America/New_York",
        str(tmp_path / "logs"),
    ]


def test_runner_executes_command_and_normalizes_results(tmp_path):
    fake = tmp_path / "fake-mvt-ios"
    fake.write_text(
        "#!/bin/sh\n"
        "out=''\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  if [ \"$1\" = '--output' ]; then shift; out=\"$1\"; fi\n"
        "  shift\n"
        "done\n"
        "mkdir -p \"$out\"\n"
        "printf '{\"mvt_version\":\"test-version\"}' > \"$out/info.json\"\n"
        "printf '[{\"level\":\"CRITICAL\",\"module\":\"fake\",\"message\":\"hit\",\"event_time\":\"\"}]' > \"$out/alerts.json\"\n",
        encoding="utf-8",
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)

    runner_input = RunnerInput(
        case_id="case-1",
        acquisition_id="acq-1",
        platform="ios",
        command="ios_backup",
        target_path=tmp_path / "backup",
        results_path=tmp_path / "out",
    )

    summary = MVTProductizationRunner(
        executable_overrides={"mvt-ios": os.fspath(fake)}
    ).run(runner_input)

    assert summary.status == "completed"
    assert summary.mvt_version == "test-version"
    assert summary.alert_counts["CRITICAL"] == 1
