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

## Chibitek Requirements

- Stiki SSO remains the only identity path for the future SaaS surface.
- Every tenant-scoped SaaS table needs RLS, timestamps, and `deleted_at`.
- Raw forensic artifacts are sensitive and must not be logged in application
  telemetry.
- Mochii follow-up tasks should reference artifact IDs and alert summaries, not
  copy full device data into task descriptions.
