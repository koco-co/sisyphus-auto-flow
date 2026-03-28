"""Contract testing plugin tests."""

from __future__ import annotations

import pytest


def test_contract_validation_can_be_enabled_from_config() -> None:
    """Contract validation should be opt-in from config and validate payload shape when enabled."""
    from sisyphus_auto_flow.plugins.contract_testing import ContractValidator

    schema = {
        "required": ["id", "name"],
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
        },
    }

    disabled = ContractValidator.from_config({})
    disabled.validate_response({"unexpected": True}, schema)

    enabled = ContractValidator.from_config({"harness": {"contract": {"enabled": True}}})
    enabled.validate_response({"id": 1, "name": "demo"}, schema)

    with pytest.raises(AssertionError, match="缺少必填字段"):
        enabled.validate_response({"id": 1}, schema)


def test_contract_validator_reports_optional_provider_availability() -> None:
    """The contract plugin should expose whether optional schemathesis support is installed."""
    from sisyphus_auto_flow.plugins.contract_testing import schemathesis_available

    assert isinstance(schemathesis_available(), bool)
