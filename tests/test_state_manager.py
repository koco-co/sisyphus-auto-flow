"""Tests for state manager - written first (TDD RED phase)."""

from pathlib import Path

import pytest

from scripts.state_manager import (
    WaveStatus,
    advance_wave,
    archive_session,
    init_session,
    resume_session,
)

# ---------------------------------------------------------------------------
# TestInitSession
# ---------------------------------------------------------------------------


class TestInitSession:
    def test_creates_state_file(self, tmp_path: Path) -> None:
        """init_session creates .autoflow/state.json in the project root."""
        init_session(tmp_path, "test.har")
        state_file = tmp_path / ".autoflow" / "state.json"
        assert state_file.exists()

    def test_state_has_session_id(self, tmp_path: Path) -> None:
        """session_id starts with 'af_'."""
        state = init_session(tmp_path, "test.har")
        assert state.session_id.startswith("af_")

    def test_initial_wave_is_zero(self, tmp_path: Path) -> None:
        """current_wave == 0 and all 4 waves are PENDING."""
        state = init_session(tmp_path, "test.har")
        assert state.current_wave == 0
        assert len(state.waves) == 4
        for key in ("1", "2", "3", "4"):
            assert key in state.waves
            assert state.waves[key].status == WaveStatus.PENDING

    def test_raises_on_existing_session(self, tmp_path: Path) -> None:
        """A second init_session call raises ValueError containing 'existing session'."""
        init_session(tmp_path, "test.har")
        with pytest.raises(ValueError, match="existing session"):
            init_session(tmp_path, "test.har")


# ---------------------------------------------------------------------------
# TestAdvanceWave
# ---------------------------------------------------------------------------


class TestAdvanceWave:
    def test_advances_to_next_wave(self, tmp_path: Path) -> None:
        """After init, advance_wave(1) sets current_wave=1 and wave '1' COMPLETED."""
        init_session(tmp_path, "test.har")
        data = {"agents": ["agent_a"], "results": "ok"}
        state = advance_wave(tmp_path, 1, data=data)

        assert state.current_wave == 1
        assert state.waves["1"].status == WaveStatus.COMPLETED
        assert state.waves["1"].completed_at is not None
        assert state.waves["1"].data == data

    def test_raises_on_out_of_order(self, tmp_path: Path) -> None:
        """After init (current_wave=0), advance_wave(3) raises ValueError('out of order')."""
        init_session(tmp_path, "test.har")
        with pytest.raises(ValueError, match="out of order"):
            advance_wave(tmp_path, 3)


# ---------------------------------------------------------------------------
# TestResumeSession
# ---------------------------------------------------------------------------


class TestResumeSession:
    def test_returns_state(self, tmp_path: Path) -> None:
        """After init+advance(1), resume returns state with current_wave=1."""
        init_session(tmp_path, "test.har")
        advance_wave(tmp_path, 1)
        state = resume_session(tmp_path)

        assert state is not None
        assert state.current_wave == 1

    def test_returns_none_when_no_session(self, tmp_path: Path) -> None:
        """When no state.json exists, resume returns None."""
        result = resume_session(tmp_path)
        assert result is None


# ---------------------------------------------------------------------------
# TestArchiveSession
# ---------------------------------------------------------------------------


class TestArchiveSession:
    def test_moves_to_history(self, tmp_path: Path) -> None:
        """After full run (init + 4 advances), archive moves files to history/{session_id}/."""
        state = init_session(tmp_path, "test.har")
        session_id = state.session_id

        for wave_num in range(1, 5):
            advance_wave(tmp_path, wave_num)

        history_dir = archive_session(tmp_path)

        assert history_dir is not None
        assert history_dir == tmp_path / ".autoflow" / "history" / session_id
        assert history_dir.exists()
        # state.json should have moved to history
        assert (history_dir / "state.json").exists()
        # state.json should no longer be at original location
        assert not (tmp_path / ".autoflow" / "state.json").exists()
