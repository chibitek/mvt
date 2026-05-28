# MVT Productization

This fork keeps the Mobile Verification Toolkit forensic core close to upstream
and adds Chibitek productization work around the existing output contract.

## Boundary

The first SaaS boundary is MVT's existing results directory:

- `info.json`
- per-module `*.json`
- per-module `*_detected.json`
- `alerts.json`
- `timeline.csv`
- `alerts_timeline.csv`
- `command.log`

The raw files are preserved unchanged. Chibitek services ingest a normalized run
summary beside those artifacts instead of rewriting MVT modules first.

## Runner Contract

The additive Python package `mvt.productization` exposes:

- `RunnerInput`
- `RunnerOptions`
- `MVTProductizationRunner`
- `normalize_results`
- tenant-scoped domain records for cases, devices, acquisitions, runs, artifacts,
  alerts, timeline events, and reviewer notes
- `build_run_ingestion_records` to convert normalized summaries into
  tenant-scoped artifact and alert records
- `build_event` for tenant-scoped event envelopes
- `SCHEMA_SQL` and `validate_schema_contract` for the initial PostgreSQL/RLS
  storage contract
- `MCP_TOOL_CONTRACTS` for the initial agent/tool surface

Supported managed commands:

| Contract command | MVT executable | MVT subcommand |
| --- | --- | --- |
| `ios_backup` | `mvt-ios` | `check-backup` |
| `ios_fs` | `mvt-ios` | `check-fs` |
| `android_backup` | `mvt-android` | `check-backup` |
| `android_androidqf` | `mvt-android` | `check-androidqf` |
| `android_bugreport` | `mvt-android` | `check-bugreport` |
| `android_intrusion_logs` | `mvt-android` | `check-intrusion-logs` |

Example service input:

```json
{
  "caseId": "case_123",
  "acquisitionId": "acq_123",
  "platform": "android",
  "command": "android_intrusion_logs",
  "targetPath": "/evidence/case_123/intrusion-logs",
  "resultsPath": "/runs/run_123/results",
  "iocFiles": ["/iocs/current.stix2"],
  "options": {
    "timezone": "America/New_York",
    "verbose": true
  }
}
```

Normalized summary shape:

```json
{
  "runId": "run_123",
  "status": "completed",
  "startedAt": "2026-05-28T00:00:00+00:00",
  "completedAt": "2026-05-28T00:01:00+00:00",
  "mvtVersion": "2026.5.12",
  "command": ["mvt-android", "check-intrusion-logs"],
  "artifactRefs": [],
  "alertCounts": {
    "INFORMATIONAL": 0,
    "LOW": 0,
    "MEDIUM": 0,
    "HIGH": 0,
    "CRITICAL": 0
  },
  "timelineCount": 0,
  "moduleResultCount": 0,
  "alerts": [],
  "error": null
}
```

## SaaS Phases

1. Repo baseline and upstream hygiene.
2. MVT runner contract and artifact normalization.
3. Case/project model and secure storage.
4. Workflow UI for intake, runs, alerts, and timelines.
5. Stiki auth, tenant isolation, audit events, and role gates.
6. Mochii/Task Engine integration and MCP tools.
7. Production hardening, retention, monitoring, and release process.

## MCP Tools

Initial tool names:

- `list_mvt_cases`
- `get_mvt_run`
- `list_mvt_alerts`
- `create_mochii_task_from_mvt_alert`

All tools require `tenantId`; implementations must set database tenant context
before reading or writing data.

## Chibitek Requirements

- Stiki SSO remains the only identity path for the future SaaS surface.
- Every tenant-scoped SaaS table needs RLS, timestamps, and `deleted_at`.
- The initial storage contract covers `mvt_cases`, `mvt_devices`,
  `mvt_acquisitions`, `mvt_analysis_runs`, `mvt_artifacts`, `mvt_alerts`,
  `mvt_timeline_events`, `mvt_reviewer_notes`, and `mvt_activity_events`.
- Event payloads must include tenant scope. `build_event` adds `tenantId` and
  rejects payloads whose tenant does not match the envelope.
- Raw forensic artifacts are sensitive and must not be logged in application
  telemetry.
- Mochii follow-up tasks should reference artifact IDs and alert summaries, not
  copy full device data into task descriptions.
