"""Wave checkpoint state manager for sisyphus-autoflow sessions."""

import shutil
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Enums & Models
# ---------------------------------------------------------------------------


class WaveStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class WaveState(BaseModel):
    status: WaveStatus = WaveStatus.PENDING
    started_at: str | None = None
    completed_at: str | None = None
    agents: list[str] = []
    data: dict = {}


class UserConfirmation(BaseModel):
    confirmed: bool = False
    modifications: list[str] = []
    confirmed_at: str | None = None


class SessionState(BaseModel):
    session_id: str
    source_har: str
    current_wave: int = 0
    waves: dict[str, WaveState] = {}
    user_confirmations: dict[str, UserConfirmation] = {}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _state_dir(project_root: Path) -> Path:
    return project_root / ".autoflow"


def _state_file(project_root: Path) -> Path:
    return _state_dir(project_root) / "state.json"


def _read_state(project_root: Path) -> SessionState | None:
    path = _state_file(project_root)
    if not path.exists():
        return None
    try:
        return SessionState.model_validate_json(path.read_text())
    except Exception as exc:
        raise ValueError(f"Failed to read state file: {exc}") from exc


def _write_state(project_root: Path, state: SessionState) -> None:
    path = _state_file(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def init_session(project_root: Path, har_filename: str) -> SessionState:
    """Create a new autoflow session with 4 pending waves.

    Raises:
        ValueError: If a session already exists in project_root.
    """
    state_dir = _state_dir(project_root)
    state_dir.mkdir(parents=True, exist_ok=True)

    if _state_file(project_root).exists():
        raise ValueError("existing session found — archive or remove it first")

    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    session_id = f"af_{timestamp}"

    waves: dict[str, WaveState] = {
        "1": WaveState(),
        "2": WaveState(),
        "3": WaveState(),
        "4": WaveState(),
    }

    state = SessionState(
        session_id=session_id,
        source_har=har_filename,
        waves=waves,
    )

    _write_state(project_root, state)
    return state


def advance_wave(
    project_root: Path,
    wave: int,
    data: dict | None = None,
) -> SessionState:
    """Advance the session to the next wave, marking it COMPLETED.

    Args:
        project_root: Root directory containing .autoflow/.
        wave: The wave number to complete (must equal current_wave + 1).
        data: Optional result data to store with the wave.

    Raises:
        ValueError: If no session exists or wave is out of order.
    """
    state = _read_state(project_root)
    if state is None:
        raise ValueError("No active session found")

    expected = state.current_wave + 1
    if wave != expected:
        raise ValueError(
            f"Wave {wave} is out of order — expected wave {expected}"
        )

    completed_wave = state.waves[str(wave)].model_copy(
        update={
            "status": WaveStatus.COMPLETED,
            "completed_at": _now_iso(),
            "data": data or {},
        }
    )

    updated_waves = {**state.waves, str(wave): completed_wave}

    new_state = state.model_copy(
        update={
            "current_wave": wave,
            "waves": updated_waves,
        }
    )

    _write_state(project_root, new_state)
    return new_state


def resume_session(project_root: Path) -> SessionState | None:
    """Load and return the current session state, or None if none exists."""
    return _read_state(project_root)


def archive_session(project_root: Path) -> Path | None:
    """Move all .autoflow files (except history/) into .autoflow/history/{session_id}/.

    Returns:
        The history directory path, or None if no active session.
    """
    state = _read_state(project_root)
    if state is None:
        return None

    state_dir = _state_dir(project_root)
    history_dir = state_dir / "history" / state.session_id
    history_dir.mkdir(parents=True, exist_ok=True)

    for item in state_dir.iterdir():
        if item.name == "history":
            continue
        shutil.move(str(item), str(history_dir / item.name))

    return history_dir
