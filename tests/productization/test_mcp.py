import pytest

from mvt.productization import (
    MCP_TOOL_CONTRACTS,
    MCP_TOOL_NAMES,
    get_tool_contract,
    validate_tool_contracts,
)


def test_mcp_tool_contracts_match_public_plan():
    validate_tool_contracts()

    assert tuple(contract.name for contract in MCP_TOOL_CONTRACTS) == MCP_TOOL_NAMES
    assert "create_mochii_task_from_mvt_alert" in MCP_TOOL_NAMES


def test_tool_contract_exports_input_schema():
    contract = get_tool_contract("list_mvt_alerts")
    data = contract.to_dict()

    assert data["inputSchema"]["required"] == ["tenantId"]
    assert data["inputSchema"]["properties"]["level"]["enum"] == [
        "INFORMATIONAL",
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]
    assert data["inputSchema"]["additionalProperties"] is False


def test_get_tool_contract_rejects_unknown_tool():
    with pytest.raises(ValueError, match="Unknown MVT MCP tool"):
        get_tool_contract("delete_everything")
