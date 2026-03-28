"""Regression tests for the default HAR parser output."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sisyphus_auto_flow.parsers.har_parser import parse_har_file

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


def test_default_parse_har_file_is_deterministic_for_same_input(tmp_path: Path) -> None:
    """Default parser output should stay stable for the same HAR input."""
    har_path = _write_sample_har(tmp_path / "sample.har")

    first = parse_har_file(har_path)
    second = parse_har_file(har_path)

    first.pop("parsed_at")
    second.pop("parsed_at")
    assert first == second
    assert [request["depends_on"] for request in first["requests"]] == [None, 1]


def test_metadata_endpoints_resolve_to_metadata_module(tmp_path: Path) -> None:
    """Metadata service endpoints should not fall back to the unmapped bucket."""
    har_path = tmp_path / "metadata.har"
    har_path.write_text(
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
                                "url": "https://example.com/dmetadata/v1/syncTask/pageTask",
                                "httpVersion": "HTTP/1.1",
                                "headers": [{"name": "Content-Type", "value": "application/json"}],
                                "queryString": [],
                                "postData": {
                                    "mimeType": "application/json",
                                    "text": json.dumps({"current": 1, "size": 20}),
                                },
                            },
                            "response": {
                                "status": 200,
                                "statusText": "OK",
                                "headers": [{"name": "Content-Type", "value": "application/json"}],
                                "content": {
                                    "size": 15,
                                    "mimeType": "application/json",
                                    "text": json.dumps({"data": []}),
                                },
                            },
                            "timings": {"send": 1, "wait": 2, "receive": 3},
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    result = parse_har_file(har_path)
    request = result["requests"][0]

    assert request["module"] == "metadata"
    assert request["module_api_dir"] == "metadata"
    assert request["module_description"] == "元数据中心"
