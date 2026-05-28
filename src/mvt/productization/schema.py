"""SQL contract for the Chibitek MVT SaaS storage layer."""

from __future__ import annotations

PRODUCTIZATION_TABLES = (
    "mvt_cases",
    "mvt_devices",
    "mvt_acquisitions",
    "mvt_analysis_runs",
    "mvt_artifacts",
    "mvt_alerts",
    "mvt_timeline_events",
    "mvt_reviewer_notes",
    "mvt_activity_events",
)

SCHEMA_SQL = """
create table if not exists public.mvt_cases (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null,
    title text not null,
    status text not null default 'open',
    opened_by_profile_id uuid,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);

create table if not exists public.mvt_devices (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null,
    case_id uuid not null references public.mvt_cases(id),
    platform text not null,
    label text not null,
    owner_reference text,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);

create table if not exists public.mvt_acquisitions (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null,
    case_id uuid not null references public.mvt_cases(id),
    device_id uuid not null references public.mvt_devices(id),
    acquisition_type text not null,
    source_uri text not null,
    captured_at timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);

create table if not exists public.mvt_analysis_runs (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null,
    case_id uuid not null references public.mvt_cases(id),
    acquisition_id uuid not null references public.mvt_acquisitions(id),
    status text not null default 'queued',
    command jsonb not null default '[]'::jsonb,
    mvt_version text,
    started_at timestamptz,
    completed_at timestamptz,
    error text,
    summary jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);

create table if not exists public.mvt_artifacts (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null,
    run_id uuid not null references public.mvt_analysis_runs(id),
    name text not null,
    path text not null,
    kind text not null,
    size_bytes bigint not null default 0,
    sha256 text not null,
    storage_uri text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);

create table if not exists public.mvt_alerts (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null,
    run_id uuid not null references public.mvt_analysis_runs(id),
    level text not null,
    module text not null,
    message text not null,
    event_time text not null default '',
    matched_indicator jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);

create table if not exists public.mvt_timeline_events (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null,
    run_id uuid not null references public.mvt_analysis_runs(id),
    timestamp text not null,
    module text not null,
    event text not null,
    data text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);

create table if not exists public.mvt_reviewer_notes (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null,
    case_id uuid not null references public.mvt_cases(id),
    run_id uuid references public.mvt_analysis_runs(id),
    alert_id uuid references public.mvt_alerts(id),
    author_profile_id uuid,
    body text not null,
    visibility text not null default 'internal',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);

create table if not exists public.mvt_activity_events (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null,
    event_type text not null,
    entity_type text not null,
    entity_id uuid not null,
    actor_profile_id uuid,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz
);

create index if not exists idx_mvt_cases_tenant_status
    on public.mvt_cases(tenant_id, status) where deleted_at is null;
create index if not exists idx_mvt_devices_tenant_case
    on public.mvt_devices(tenant_id, case_id) where deleted_at is null;
create index if not exists idx_mvt_acquisitions_tenant_case
    on public.mvt_acquisitions(tenant_id, case_id) where deleted_at is null;
create index if not exists idx_mvt_analysis_runs_tenant_case
    on public.mvt_analysis_runs(tenant_id, case_id, status) where deleted_at is null;
create index if not exists idx_mvt_artifacts_tenant_run
    on public.mvt_artifacts(tenant_id, run_id) where deleted_at is null;
create index if not exists idx_mvt_alerts_tenant_run_level
    on public.mvt_alerts(tenant_id, run_id, level) where deleted_at is null;
create index if not exists idx_mvt_timeline_events_tenant_run
    on public.mvt_timeline_events(tenant_id, run_id) where deleted_at is null;
create index if not exists idx_mvt_reviewer_notes_tenant_case
    on public.mvt_reviewer_notes(tenant_id, case_id) where deleted_at is null;
create index if not exists idx_mvt_activity_events_tenant_type
    on public.mvt_activity_events(tenant_id, event_type, created_at desc)
    where deleted_at is null;

alter table public.mvt_cases enable row level security;
alter table public.mvt_devices enable row level security;
alter table public.mvt_acquisitions enable row level security;
alter table public.mvt_analysis_runs enable row level security;
alter table public.mvt_artifacts enable row level security;
alter table public.mvt_alerts enable row level security;
alter table public.mvt_timeline_events enable row level security;
alter table public.mvt_reviewer_notes enable row level security;
alter table public.mvt_activity_events enable row level security;

create policy "tenant scoped mvt_cases" on public.mvt_cases
    for all using (tenant_id::text = current_setting('app.current_tenant_id', true))
    with check (tenant_id::text = current_setting('app.current_tenant_id', true));
create policy "tenant scoped mvt_devices" on public.mvt_devices
    for all using (tenant_id::text = current_setting('app.current_tenant_id', true))
    with check (tenant_id::text = current_setting('app.current_tenant_id', true));
create policy "tenant scoped mvt_acquisitions" on public.mvt_acquisitions
    for all using (tenant_id::text = current_setting('app.current_tenant_id', true))
    with check (tenant_id::text = current_setting('app.current_tenant_id', true));
create policy "tenant scoped mvt_analysis_runs" on public.mvt_analysis_runs
    for all using (tenant_id::text = current_setting('app.current_tenant_id', true))
    with check (tenant_id::text = current_setting('app.current_tenant_id', true));
create policy "tenant scoped mvt_artifacts" on public.mvt_artifacts
    for all using (tenant_id::text = current_setting('app.current_tenant_id', true))
    with check (tenant_id::text = current_setting('app.current_tenant_id', true));
create policy "tenant scoped mvt_alerts" on public.mvt_alerts
    for all using (tenant_id::text = current_setting('app.current_tenant_id', true))
    with check (tenant_id::text = current_setting('app.current_tenant_id', true));
create policy "tenant scoped mvt_timeline_events" on public.mvt_timeline_events
    for all using (tenant_id::text = current_setting('app.current_tenant_id', true))
    with check (tenant_id::text = current_setting('app.current_tenant_id', true));
create policy "tenant scoped mvt_reviewer_notes" on public.mvt_reviewer_notes
    for all using (tenant_id::text = current_setting('app.current_tenant_id', true))
    with check (tenant_id::text = current_setting('app.current_tenant_id', true));
create policy "tenant scoped mvt_activity_events" on public.mvt_activity_events
    for all using (tenant_id::text = current_setting('app.current_tenant_id', true))
    with check (tenant_id::text = current_setting('app.current_tenant_id', true));
"""


def validate_schema_contract(sql: str = SCHEMA_SQL) -> None:
    lowered = sql.lower()
    for table in PRODUCTIZATION_TABLES:
        table_sql = _table_block(lowered, table)
        if "tenant_id uuid not null" not in table_sql:
            raise ValueError(f"{table} is missing tenant_id")
        if "created_at timestamptz" not in table_sql:
            raise ValueError(f"{table} is missing created_at")
        if "updated_at timestamptz" not in table_sql:
            raise ValueError(f"{table} is missing updated_at")
        if "deleted_at timestamptz" not in table_sql:
            raise ValueError(f"{table} is missing deleted_at")
        if f"alter table public.{table} enable row level security" not in lowered:
            raise ValueError(f"{table} is missing RLS enablement")
        if f'tenant scoped {table}' not in lowered:
            raise ValueError(f"{table} is missing tenant scoped policy")


def _table_block(sql: str, table: str) -> str:
    start = sql.find(f"create table if not exists public.{table}")
    if start == -1:
        raise ValueError(f"{table} table is missing")
    end = sql.find(");", start)
    if end == -1:
        raise ValueError(f"{table} table definition is incomplete")
    return sql[start:end]
