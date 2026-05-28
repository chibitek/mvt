"""Normalize MVT output folders for SaaS ingestion.

The productization boundary intentionally starts at MVT's existing output files.
This module summarizes those files without modifying or reinterpreting the raw
forensic artifacts.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from mvt.common.alerts import AlertLevel
from mvt.common.version import MVT_VERSION

AGGREGATE_ARTIFACTS = {
    "alerts.json",
    "alerts_timeline.csv",
    "command.log",
    "info.json",
    "timeline.csv",
}


@dataclass(frozen=True)
class ArtifactRef:
    name: str
    path: str
    kind: str
    size_bytes: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedAlert:
    level: str
    module: str
    message: str
    event_time: str
    matched_indicator: Any = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedRunSummary:
    run_id: str
    status: str
    started_at: str | None
    completed_at: str | None
    mvt_version: str
    command: list[str]
    artifact_refs: list[ArtifactRef] = field(default_factory=list)
    alert_counts: dict[str, int] = field(default_factory=dict)
    timeline_count: int = 0
    module_result_count: int = 0
    alerts: list[NormalizedAlert] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["runId"] = data.pop("run_id")
        data["startedAt"] = data.pop("started_at")
        data["completedAt"] = data.pop("completed_at")
        data["mvtVersion"] = data.pop("mvt_version")
        data["artifactRefs"] = data.pop("artifact_refs")
        data["alertCounts"] = data.pop("alert_counts")
        data["timelineCount"] = data.pop("timeline_count")
        data["moduleResultCount"] = data.pop("module_result_count")
        return data


def normalize_results(
    results_path: str | Path,
    *,
    run_id: str,
    status: str,
    command: list[str],
    started_at: str | None = None,
    completed_at: str | None = None,
    error: str | None = None,
) -> NormalizedRunSummary:
    root = Path(results_path)
    artifact_refs = _collect_artifact_refs(root)
    info = _read_json(root / "info.json", default={})
    alerts = _read_alerts(root / "alerts.json")

    return NormalizedRunSummary(
        run_id=run_id,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        mvt_version=str(info.get("mvt_version") or MVT_VERSION),
        command=command,
        artifact_refs=artifact_refs,
        alert_counts=_count_alerts(alerts),
        timeline_count=_count_csv_rows(root / "timeline.csv"),
        module_result_count=_count_module_results(root),
        alerts=alerts,
        error=error,
    )


def _collect_artifact_refs(root: Path) -> list[ArtifactRef]:
    if not root.exists():
        return []

    refs: list[ArtifactRef] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        refs.append(
            ArtifactRef(
                name=path.name,
                path=path.relative_to(root).as_posix(),
                kind=_classify_artifact(path),
                size_bytes=path.stat().st_size,
                sha256=_sha256(path),
            )
        )
    return refs


def _classify_artifact(path: Path) -> str:
    name = path.name
    if name == "alerts.json":
        return "alerts"
    if name == "alerts_timeline.csv":
        return "alerts_timeline"
    if name == "timeline.csv":
        return "timeline"
    if name == "info.json":
        return "run_info"
    if name == "command.log":
        return "log"
    if name.endswith("_detected.json"):
        return "module_detections"
    if name.endswith(".json"):
        return "module_results"
    return "artifact"


def _read_alerts(path: Path) -> list[NormalizedAlert]:
    raw_alerts = _read_json(path, default=[])
    if not isinstance(raw_alerts, list):
        return []

    alerts: list[NormalizedAlert] = []
    for item in raw_alerts:
        if not isinstance(item, dict):
            continue
        alerts.append(
            NormalizedAlert(
                level=str(item.get("level") or "UNKNOWN"),
                module=str(item.get("module") or "unknown"),
                message=str(item.get("message") or ""),
                event_time=str(item.get("event_time") or ""),
                matched_indicator=item.get("matched_indicator"),
            )
        )
    return alerts


def _count_alerts(alerts: list[NormalizedAlert]) -> dict[str, int]:
    counts = {level.name: 0 for level in AlertLevel}
    for alert in alerts:
        counts[alert.level] = counts.get(alert.level, 0) + 1
    return counts


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)

    if not rows:
        return 0
    return max(len(rows) - 1, 0)


def _count_module_results(root: Path) -> int:
    if not root.exists():
        return 0

    count = 0
    for path in root.glob("*.json"):
        if path.name in AGGREGATE_ARTIFACTS or path.name.endswith("_detected.json"):
            continue
        data = _read_json(path, default=None)
        if isinstance(data, list):
            count += len(data)
        elif isinstance(data, dict):
            count += 1
    return count


def _read_json(path: Path, *, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
