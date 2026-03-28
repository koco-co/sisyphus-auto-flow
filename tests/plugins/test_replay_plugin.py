"""Replay plugin tests."""

from __future__ import annotations

import httpx


def test_replay_store_records_and_replays_deterministically(tmp_path) -> None:
    """Recorded interactions should round-trip deterministically in replay mode."""
    from sisyphus_auto_flow.plugins.replay import ReplayMode, ReplayStore, build_replay_key

    interaction = {
        "status_code": 200,
        "headers": {"Content-Type": "application/json"},
        "body": '{"ok": true}',
    }
    key = build_replay_key("GET", "/health", params={"page": 1})

    recorder = ReplayStore(tmp_path, mode=ReplayMode.RECORD)
    recorder.record(key, interaction)

    replayer = ReplayStore(tmp_path, mode=ReplayMode.REPLAY)
    loaded = replayer.replay(key)

    assert loaded == interaction
    response = replayer.to_response(loaded, request=httpx.Request("GET", "http://example.com/health"))
    assert response.status_code == 200
    assert response.json() == {"ok": True}
