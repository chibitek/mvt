"""MCP/API tool contract for Chibitek MVT integrations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

MCP_TOOL_NAMES = (
    "list_mvt_cases",
    "get_mvt_run",
    "list_mvt_alerts",
    "create_mochii_task_from_mvt_alert",
)


@dataclass(frozen=True)
class ToolContract:
    name: str
    description: str
    required: tuple[str, ...]
    properties: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["inputSchema"] = {
            "type": "object",
            "required": list(self.required),
            "properties": self.properties,
            "additionalProperties": False,
        }
        del data["required"]
        del data["properties"]
        return data


MCP_TOOL_CONTRACTS = (
    ToolContract(
        name="list_mvt_cases",
        description="List tenant-scoped MVT cases visible to the caller.",
        required=("tenantId",),
        properties={
            "tenantId": {"type": "string"},
            "status": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 200},
        },
    ),
    ToolContract(
        name="get_mvt_run",
        description="Get one MVT analysis run summary and artifact references.",
        required=("tenantId", "runId"),
        properties={
            "tenantId": {"type": "string"},
            "runId": {"type": "string"},
        },
    ),
    ToolContract(
        name="list_mvt_alerts",
        description="List alerts for a tenant-scoped MVT case or run.",
        required=("tenantId",),
        properties={
            "tenantId": {"type": "string"},
            "caseId": {"type": "string"},
            "runId": {"type": "string"},
            "level": {
                "type": "string",
                "enum": ["INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
            },
            "limit": {"type": "integer", "minimum": 1, "maximum": 200},
        },
    ),
    ToolContract(
        name="create_mochii_task_from_mvt_alert",
        description="Create a Mochii follow-up task from a high-signal MVT alert.",
        required=("tenantId", "alertId", "projectId"),
        properties={
            "tenantId": {"type": "string"},
            "alertId": {"type": "string"},
            "projectId": {"type": "string"},
            "assigneeProfileId": {"type": "string"},
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "urgent"],
            },
        },
    ),
)


def get_tool_contract(name: str) -> ToolContract:
    for contract in MCP_TOOL_CONTRACTS:
        if contract.name == name:
            return contract
    supported = ", ".join(MCP_TOOL_NAMES)
    raise ValueError(f"Unknown MVT MCP tool {name!r}: {supported}")


def validate_tool_contracts() -> None:
    names = tuple(contract.name for contract in MCP_TOOL_CONTRACTS)
    if names != MCP_TOOL_NAMES:
        raise ValueError("MCP tool names and contracts are out of sync")
    for contract in MCP_TOOL_CONTRACTS:
        if "tenantId" not in contract.required:
            raise ValueError(f"{contract.name} must require tenantId")
        for required in contract.required:
            if required not in contract.properties:
                raise ValueError(f"{contract.name} missing property for {required}")
