"""Runner contract for managed MVT analysis jobs."""

from __future__ import annotations

import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .artifacts import NormalizedRunSummary, normalize_results

SUPPORTED_COMMANDS = {
    "ios_backup": ("mvt-ios", "check-backup"),
    "ios_fs": ("mvt-ios", "check-fs"),
    "android_backup": ("mvt-android", "check-backup"),
    "android_androidqf": ("mvt-android", "check-androidqf"),
    "android_bugreport": ("mvt-android", "check-bugreport"),
    "android_intrusion_logs": ("mvt-android", "check-intrusion-logs"),
}


@dataclass(frozen=True)
class RunnerOptions:
    module: str | None = None
    fast: bool = False
    hashes: bool = False
    verbose: bool = False
    non_interactive: bool = True
    backup_password: str | None = None
    timezone: str | None = None
    disable_update_check: bool = True
    disable_indicator_update_check: bool = True

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> "RunnerOptions":
        if not data:
            return cls()
        return cls(
            module=data.get("module"),
            fast=bool(data.get("fast", False)),
            hashes=bool(data.get("hashes", False)),
            verbose=bool(data.get("verbose", False)),
            non_interactive=bool(
                data.get("non_interactive", data.get("nonInteractive", True))
            ),
            backup_password=data.get("backup_password") or data.get("backupPassword"),
            timezone=data.get("timezone"),
            disable_update_check=bool(
                data.get("disable_update_check", data.get("disableUpdateCheck", True))
            ),
            disable_indicator_update_check=bool(
                data.get(
                    "disable_indicator_update_check",
                    data.get("disableIndicatorUpdateCheck", True),
                )
            ),
        )


@dataclass(frozen=True)
class RunnerInput:
    case_id: str
    acquisition_id: str
    platform: str
    command: str
    target_path: Path
    results_path: Path
    ioc_files: list[Path] = field(default_factory=list)
    options: RunnerOptions = field(default_factory=RunnerOptions)
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "RunnerInput":
        options = RunnerOptions.from_mapping(data.get("options"))
        case_id = data.get("case_id") or data.get("caseId")
        acquisition_id = data.get("acquisition_id") or data.get("acquisitionId")
        target_path = data.get("target_path") or data.get("targetPath")
        results_path = data.get("results_path") or data.get("resultsPath")
        if not case_id:
            raise ValueError("caseId is required")
        if not acquisition_id:
            raise ValueError("acquisitionId is required")
        if not target_path:
            raise ValueError("targetPath is required")
        if not results_path:
            raise ValueError("resultsPath is required")

        return cls(
            case_id=str(case_id),
            acquisition_id=str(acquisition_id),
            platform=str(data["platform"]),
            command=str(data["command"]),
            target_path=Path(target_path),
            results_path=Path(results_path),
            ioc_files=[
                Path(path) for path in data.get("ioc_files", data.get("iocFiles", []))
            ],
            options=options,
            run_id=str(data.get("run_id") or data.get("runId") or uuid.uuid4()),
        )


class MVTProductizationRunner:
    """Execute one MVT analysis and return a normalized SaaS summary."""

    def __init__(self, executable_overrides: dict[str, str] | None = None) -> None:
        self.executable_overrides = executable_overrides or {}

    def build_command(self, runner_input: RunnerInput) -> list[str]:
        if runner_input.command not in SUPPORTED_COMMANDS:
            supported = ", ".join(sorted(SUPPORTED_COMMANDS))
            raise ValueError(f"Unsupported MVT command {runner_input.command!r}: {supported}")

        executable, subcommand = SUPPORTED_COMMANDS[runner_input.command]
        executable = self.executable_overrides.get(executable, executable)
        options = runner_input.options

        args = [executable]
        if options.disable_update_check:
            args.append("--disable-update-check")
        if options.disable_indicator_update_check:
            args.append("--disable-indicator-update-check")

        args.append(subcommand)
        for ioc_file in runner_input.ioc_files:
            args.extend(["--iocs", str(ioc_file)])
        args.extend(["--output", str(runner_input.results_path)])

        if options.module:
            args.extend(["--module", options.module])
        if options.fast and runner_input.command in {"ios_backup", "ios_fs"}:
            args.append("--fast")
        if options.hashes and runner_input.command in {
            "ios_backup",
            "ios_fs",
            "android_androidqf",
        }:
            args.append("--hashes")
        if options.verbose:
            args.append("--verbose")
        if options.non_interactive and runner_input.command in {
            "android_backup",
            "android_androidqf",
        }:
            args.append("--non-interactive")
        if options.backup_password and runner_input.command in {
            "android_backup",
            "android_androidqf",
        }:
            args.extend(["--backup-password", options.backup_password])
        if options.timezone and runner_input.command == "android_intrusion_logs":
            args.extend(["--timezone", options.timezone])

        args.append(str(runner_input.target_path))
        return args

    def run(self, runner_input: RunnerInput) -> NormalizedRunSummary:
        runner_input.results_path.mkdir(parents=True, exist_ok=True)
        command = self.build_command(runner_input)
        started_at = _now()

        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        completed_at = _now()

        error = None
        status = "completed"
        if completed.returncode != 0:
            status = "failed"
            error = (completed.stderr or completed.stdout or "").strip()

        return normalize_results(
            runner_input.results_path,
            run_id=runner_input.run_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            command=command,
            error=error,
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
