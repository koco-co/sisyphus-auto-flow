"""CLI parse command characterization tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from click.testing import CliRunner

from sisyphus_auto_flow.cli import main


def test_parse_command_writes_normalized_output(tmp_path: Path) -> None:
    """The CLI parse command should delegate to the HAR parser and write JSON output."""
    har_path = tmp_path / "sample.har"
    output_path = tmp_path / "parsed.json"
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
                                    "size": 19,
                                    "mimeType": "application/json",
                                    "text": json.dumps({"data": {"id": 1}}),
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

    result = CliRunner().invoke(main, ["parse", str(har_path), "--output", str(output_path)])

    assert result.exit_code == 0, result.output
    assert output_path.exists()

    parsed = json.loads(output_path.read_text(encoding="utf-8"))
    assert parsed["source"] == "sample.har"
    assert parsed["filtered_entries"] == 1
    assert parsed["requests"][0]["path"] == "/dassets/v1/dataDb/batchAddDb"


def test_parse_wrapper_matches_cli_output(tmp_path: Path) -> None:
    """The agent-facing parse wrapper should produce the same normalized JSON as the CLI."""
    repo_root = Path(__file__).resolve().parents[2]
    har_path = tmp_path / "sample.har"
    cli_output = tmp_path / "cli.json"
    wrapper_output = tmp_path / "wrapper.json"
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
                                "method": "GET",
                                "url": "https://example.com/dassets/v1/dataDb/pageQuery",
                                "httpVersion": "HTTP/1.1",
                                "headers": [],
                                "queryString": [],
                            },
                            "response": {
                                "status": 200,
                                "statusText": "OK",
                                "headers": [{"name": "Content-Type", "value": "application/json"}],
                                "content": {
                                    "size": 18,
                                    "mimeType": "application/json",
                                    "text": json.dumps({"data": {"id": 7}}),
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

    cli_result = CliRunner().invoke(main, ["parse", str(har_path), "--output", str(cli_output)])
    assert cli_result.exit_code == 0, cli_result.output

    wrapper = repo_root / ".claude" / "scripts" / "parse_har.sh"
    wrapper_result = subprocess.run(
        ["bash", str(wrapper), str(har_path), str(wrapper_output)],
        capture_output=True,
        cwd=repo_root,
        text=True,
        check=False,
    )
    assert wrapper_result.returncode == 0, wrapper_result.stdout + wrapper_result.stderr

    cli_json = json.loads(cli_output.read_text(encoding="utf-8"))
    wrapper_json = json.loads(wrapper_output.read_text(encoding="utf-8"))
    cli_json.pop("parsed_at")
    wrapper_json.pop("parsed_at")
    assert wrapper_json == cli_json


def test_parse_then_plan_wrappers_support_two_step_flow(tmp_path: Path) -> None:
    """The wrapper pipeline should stage a repo-local HAR copy and keep the caller's source file."""
    repo_root = Path(__file__).resolve().parents[2]
    har_path = tmp_path / "sample.har"
    parsed_output = tmp_path / "parsed.json"
    manifest_output = tmp_path / "workflow.json"
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
                                    "size": 19,
                                    "mimeType": "application/json",
                                    "text": json.dumps({"data": {"id": 1}}),
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

    parse_wrapper = repo_root / ".claude" / "scripts" / "parse_har.sh"
    parse_result = subprocess.run(
        ["bash", str(parse_wrapper), str(har_path), str(parsed_output)],
        capture_output=True,
        cwd=repo_root,
        text=True,
        check=False,
    )
    assert parse_result.returncode == 0, parse_result.stdout + parse_result.stderr
    assert parsed_output.exists()
    assert har_path.exists()

    plan_wrapper = repo_root / ".claude" / "scripts" / "plan_har_workflow.sh"
    plan_result = subprocess.run(
        ["bash", str(plan_wrapper), str(parsed_output), "release_6.2.x", str(manifest_output)],
        capture_output=True,
        cwd=repo_root,
        text=True,
        check=False,
    )
    assert plan_result.returncode == 0, plan_result.stdout + plan_result.stderr
    assert manifest_output.exists()

    manifest = json.loads(manifest_output.read_text(encoding="utf-8"))
    assert manifest["source_har"] == "sample.har"
    assert manifest["release"] == "release_6.2.x"


def test_generate_wrapper_creates_pytest_file(tmp_path: Path) -> None:
    """The agent-facing generation wrapper should create a pytest file from a scenario JSON payload."""
    repo_root = Path(__file__).resolve().parents[2]
    scenario_path = tmp_path / "scenario.json"
    output_dir = tmp_path / "generated"
    scenario_path.write_text(
        json.dumps(
            {
                "name": "smoke",
                "description": "Smoke scenario",
                "module": "assets",
                "epic": "数据资产",
                "feature": "Smoke",
                "tags": ["crud"],
                "steps": [
                    {
                        "name": "ping",
                        "description": "ping step",
                        "request": {"method": "GET", "url": "/health"},
                        "assertions": [
                            {
                                "type": "status_code",
                                "target": "status_code",
                                "expected": 200,
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    wrapper = repo_root / ".claude" / "scripts" / "generate_tests.sh"
    result = subprocess.run(
        ["bash", str(wrapper), str(scenario_path), str(output_dir)],
        capture_output=True,
        cwd=repo_root,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    generated_file = output_dir / "test_assets_smoke.py"
    assert generated_file.exists()
    assert "BaseAPITest" in generated_file.read_text(encoding="utf-8")
