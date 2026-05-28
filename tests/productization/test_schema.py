import pytest

from mvt.productization import (
    PRODUCTIZATION_TABLES,
    SCHEMA_SQL,
    validate_schema_contract,
)


def test_schema_contract_covers_all_productization_tables():
    validate_schema_contract()

    lowered = SCHEMA_SQL.lower()
    for table in PRODUCTIZATION_TABLES:
        assert f"create table if not exists public.{table}" in lowered
        assert f"alter table public.{table} enable row level security" in lowered
        assert f'tenant scoped {table}' in lowered


def test_schema_contract_rejects_missing_soft_delete():
    broken_sql = SCHEMA_SQL.replace("    deleted_at timestamptz\n);", ");", 1)

    with pytest.raises(ValueError, match="mvt_cases is missing deleted_at"):
        validate_schema_contract(broken_sql)
