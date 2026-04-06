"""Tests for HAR parser - written first (TDD RED phase)."""

import base64
import json
from pathlib import Path

import pytest

from scripts.har_parser import (
    HarEntry,
    HarRequest,
    HarResponse,
    ParsedResult,
    dedup_entries,
    filter_entries,
    match_repo,
    parse_har,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(
    method: str = "POST",
    url: str = "http://172.16.115.247/dassets/v1/datamap/recentQuery",
    req_body: str = "{}",
    resp_status: int = 200,
    resp_body: str = '{"ok":true}',
    resp_mime: str = "application/json",
    time_ms: float = 50,
) -> dict:
    return {
        "time": time_ms,
        "request": {
            "method": method,
            "url": url,
            "httpVersion": "HTTP/1.1",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "queryString": [],
            "postData": {"mimeType": "application/json", "text": req_body},
            "headersSize": -1,
            "bodySize": len(req_body),
        },
        "response": {
            "status": resp_status,
            "statusText": "OK",
            "httpVersion": "HTTP/1.1",
            "headers": [{"name": "Content-Type", "value": resp_mime}],
            "content": {"mimeType": resp_mime, "text": resp_body},
            "redirectURL": "",
            "headersSize": -1,
            "bodySize": -1,
        },
        "cache": {},
        "timings": {"send": 0, "wait": time_ms, "receive": 0},
    }


def _load_har_entries(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    return data["log"]["entries"]


# ---------------------------------------------------------------------------
# TestHarModels
# ---------------------------------------------------------------------------


class TestHarModels:
    def test_har_request_from_entry(self) -> None:
        """Parse raw dict into HarRequest and verify method / url / body."""
        raw = _make_entry(method="POST", req_body='{"keyword":"test"}')
        req = HarRequest(**raw["request"])

        assert req.method == "POST"
        assert "recentQuery" in req.url
        assert req.body == {"keyword": "test"}

    def test_har_response_from_entry(self) -> None:
        """Parse raw dict into HarResponse and verify status / body."""
        raw = _make_entry(resp_status=200, resp_body='{"code":1,"success":true}')
        resp = HarResponse(**raw["response"])

        assert resp.status == 200
        assert resp.body == {"code": 1, "success": True}

    def test_har_response_base64_encoded(self) -> None:
        """Handle base64-encoded response content transparently."""
        payload = {"data": "binary-like"}
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()
        raw_resp = {
            "status": 200,
            "statusText": "OK",
            "httpVersion": "HTTP/1.1",
            "headers": [{"name": "Content-Type", "value": "application/json"}],
            "content": {
                "mimeType": "application/json",
                "text": encoded,
                "encoding": "base64",
            },
            "redirectURL": "",
            "headersSize": -1,
            "bodySize": -1,
        }
        resp = HarResponse(**raw_resp)
        assert resp.body == payload


# ---------------------------------------------------------------------------
# TestFilterEntries
# ---------------------------------------------------------------------------


class TestFilterEntries:
    def test_keeps_json_api_requests(self, sample_har_path: Path) -> None:
        """sample.har has 3 clean JSON API entries; all should survive filtering."""
        entries_raw = _load_har_entries(sample_har_path)
        entries = [HarEntry(**e) for e in entries_raw]
        filtered = filter_entries(entries)
        assert len(filtered) == 3

    def test_drops_static_resources(self, sample_dirty_har_path: Path) -> None:
        """After filtering, no paths with .js / .css extensions should remain."""
        entries_raw = _load_har_entries(sample_dirty_har_path)
        entries = [HarEntry(**e) for e in entries_raw]
        filtered = filter_entries(entries)

        paths = [e.request.path for e in filtered]
        assert not any(p.endswith(".js") or p.endswith(".css") for p in paths)

    def test_drops_websocket(self, sample_dirty_har_path: Path) -> None:
        """WebSocket upgrade responses (status 101) must be dropped."""
        entries_raw = _load_har_entries(sample_dirty_har_path)
        entries = [HarEntry(**e) for e in entries_raw]
        filtered = filter_entries(entries)

        statuses = [e.response.status for e in filtered]
        assert 101 not in statuses

    def test_drops_hot_update(self, sample_dirty_har_path: Path) -> None:
        """Paths containing 'hot-update' noise must be dropped."""
        entries_raw = _load_har_entries(sample_dirty_har_path)
        entries = [HarEntry(**e) for e in entries_raw]
        filtered = filter_entries(entries)

        paths = [e.request.path for e in filtered]
        assert not any("hot-update" in p for p in paths)


# ---------------------------------------------------------------------------
# TestDedupEntries
# ---------------------------------------------------------------------------


class TestDedupEntries:
    def test_merges_same_method_path(self, sample_dirty_har_path: Path) -> None:
        """Duplicate (method, path, status, body_hash) entries should collapse."""
        entries_raw = _load_har_entries(sample_dirty_har_path)
        entries = [HarEntry(**e) for e in entries_raw]
        filtered = filter_entries(entries)
        deduped = dedup_entries(filtered)

        recent_query_entries = [
            e for e in deduped if "recentQuery" in e.request.path
        ]
        # There are 3 distinct (method, path, status, body_hash) combos for recentQuery
        # (empty body/200, keyword body/200, empty body/500) → at most 3
        assert len(recent_query_entries) <= 3

    def test_keeps_different_status_codes(self, sample_dirty_har_path: Path) -> None:
        """Entries with the same path but different status codes must both survive."""
        entries_raw = _load_har_entries(sample_dirty_har_path)
        entries = [HarEntry(**e) for e in entries_raw]
        filtered = filter_entries(entries)
        deduped = dedup_entries(filtered)

        recent_query_entries = [
            e for e in deduped if "recentQuery" in e.request.path
        ]
        statuses = {e.response.status for e in recent_query_entries}
        assert 200 in statuses
        assert 500 in statuses


# ---------------------------------------------------------------------------
# TestMatchRepo
# ---------------------------------------------------------------------------


class TestMatchRepo:
    def test_matches_dassets_prefix(self, sample_repo_profiles_path: Path) -> None:
        import yaml

        profiles_data = yaml.safe_load(sample_repo_profiles_path.read_text())
        profiles = profiles_data["profiles"]

        name, branch = match_repo("/dassets/v1/datamap/recentQuery", profiles)
        assert name == "dt-center-assets"
        assert branch == "release_6.2.x"

    def test_matches_dmetadata_prefix(self, sample_repo_profiles_path: Path) -> None:
        import yaml

        profiles_data = yaml.safe_load(sample_repo_profiles_path.read_text())
        profiles = profiles_data["profiles"]

        name, branch = match_repo("/dmetadata/v1/syncTask/pageTask", profiles)
        assert name == "dt-center-metadata"
        assert branch == "release_6.2.x"

    def test_returns_none_for_unknown_prefix(
        self, sample_repo_profiles_path: Path
    ) -> None:
        import yaml

        profiles_data = yaml.safe_load(sample_repo_profiles_path.read_text())
        profiles = profiles_data["profiles"]

        name, branch = match_repo("/unknown/v1/something", profiles)
        assert name is None
        assert branch is None


# ---------------------------------------------------------------------------
# TestParseHar
# ---------------------------------------------------------------------------


class TestParseHar:
    def test_full_parse(
        self, sample_har_path: Path, sample_repo_profiles_path: Path
    ) -> None:
        """Full parse of sample.har should yield 3 endpoints and correct metadata."""
        result = parse_har(sample_har_path, sample_repo_profiles_path)

        assert isinstance(result, ParsedResult)
        assert len(result.endpoints) == 3
        assert result.base_url == "http://172.16.115.247"
        services = result.summary.services
        assert "dassets" in services
        assert "dmetadata" in services

    def test_endpoint_has_matched_repo(
        self, sample_har_path: Path, sample_repo_profiles_path: Path
    ) -> None:
        """Each /dassets/… endpoint must carry matched_repo=dt-center-assets."""
        result = parse_har(sample_har_path, sample_repo_profiles_path)

        dassets_endpoints = [
            e for e in result.endpoints if e.service == "dassets"
        ]
        assert len(dassets_endpoints) > 0
        for ep in dassets_endpoints:
            assert ep.matched_repo == "dt-center-assets"

    def test_raises_on_invalid_har(self, tmp_path: Path) -> None:
        """A non-JSON file should raise ValueError('Invalid HAR')."""
        bad_file = tmp_path / "bad.har"
        bad_file.write_text("this is not json at all")

        with pytest.raises(ValueError, match="Invalid HAR"):
            parse_har(bad_file, None)

    def test_raises_on_empty_entries(self, tmp_path: Path) -> None:
        """A valid HAR with zero entries should raise ValueError('No entries')."""
        empty_har = {"log": {"version": "1.2", "entries": []}}
        empty_file = tmp_path / "empty.har"
        empty_file.write_text(json.dumps(empty_har))

        with pytest.raises(ValueError, match="No entries"):
            parse_har(empty_file, None)
