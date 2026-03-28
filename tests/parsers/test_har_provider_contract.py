"""HAR provider contract tests."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


def _write_sample_har(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "log": {
                    "version": "1.2",
                    "creator": {"name": "pytest", "version": "1.0"},
                    "entries": [
                        {
                            "startedDateTime": "2026-03-28T00:00:00.000Z",
                            "request": {
                                "method": "POST",
                                "url": "https://example.com/dassets/v1/dataDb/batchAddDb",
                                "httpVersion": "HTTP/1.1",
                                "headers": [{"name": "Content-Type", "value": "application/json"}],
                                "queryString": [],
                                "postData": {
                                    "mimeType": "application/json",
                                    "text": json.dumps({"datasource_name": "demo"}),
                                },
                            },
                            "response": {
                                "status": 200,
                                "statusText": "OK",
                                "headers": [{"name": "Content-Type", "value": "application/json"}],
                                "content": {
                                    "size": 34,
                                    "mimeType": "application/json",
                                    "text": json.dumps({"data": {"id": "asset-123"}}),
                                },
                            },
                            "timings": {"send": 1, "wait": 2, "receive": 3},
                        },
                        {
                            "startedDateTime": "2026-03-28T00:00:01.000Z",
                            "request": {
                                "method": "GET",
                                "url": "https://example.com/dassets/v1/dataDb/detail/asset-123",
                                "httpVersion": "HTTP/1.1",
                                "headers": [],
                                "queryString": [],
                            },
                            "response": {
                                "status": 200,
                                "statusText": "OK",
                                "headers": [{"name": "Content-Type", "value": "application/json"}],
                                "content": {
                                    "size": 49,
                                    "mimeType": "application/json",
                                    "text": json.dumps({"data": {"id": "asset-123", "name": "demo"}}),
                                },
                            },
                            "timings": {"send": 1, "wait": 2, "receive": 3},
                        },
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    return path


def test_custom_provider_returns_normalized_requests(tmp_path: Path) -> None:
    """The default custom provider should expose normalized request data and stable dependencies."""
    from sisyphus_auto_flow.parsers.adapters.custom_adapter import CustomHarProvider

    har_path = _write_sample_har(tmp_path / "sample.har")

    result = CustomHarProvider().parse(har_path)

    assert result.source == "sample.har"
    assert result.total_entries == 2
    assert len(result.requests) == 2
    assert result.requests[0].method == "POST"
    assert result.requests[0].path == "/dassets/v1/dataDb/batchAddDb"
    assert result.requests[0].module == "assets"
    assert result.requests[1].depends_on == 1
    assert result.requests[1].path.endswith("asset-123")


def test_parse_har_file_accepts_provider_and_writes_output(tmp_path: Path) -> None:
    """The top-level parser should accept a provider object and persist its normalized output."""
    from sisyphus_auto_flow.parsers.adapters.custom_adapter import CustomHarProvider
    from sisyphus_auto_flow.parsers.har_parser import parse_har_file

    har_path = _write_sample_har(tmp_path / "sample.har")
    output_path = tmp_path / "parsed.json"

    result = parse_har_file(har_path, output_path, provider=CustomHarProvider())

    assert output_path.exists()
    assert result["requests"][1]["depends_on"] == 1


def test_hario_core_provider_handles_missing_dependency(tmp_path: Path) -> None:
    """The optional hario-core adapter should fail explicitly when the dependency is unavailable."""
    from sisyphus_auto_flow.parsers.adapters.hario_core_adapter import HarioCoreHarProvider

    har_path = _write_sample_har(tmp_path / "sample.har")
    provider = HarioCoreHarProvider()

    if provider.is_available():
        result = provider.parse(har_path)
        assert result.total_entries == 2
    else:
        with pytest.raises(RuntimeError, match="hario-core"):
            provider.parse(har_path)
