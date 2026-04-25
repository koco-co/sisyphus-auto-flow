"""Integration test: simulate wave orchestration with mocked agents."""
from pathlib import Path

import pytest

from scripts.har_parser import parse_har
from scripts.state_manager import WaveStatus, init_session, advance_wave, resume_session

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestFlowOrchestration:
    """验证编排逻辑在 mock 环境下的完整性。"""

    def test_precheck_to_wave1(self, tmp_path: Path) -> None:
        """预检阶段到 Wave 1 完成：HAR 校验 → 解析 → state 推进。"""
        har_path = FIXTURES_DIR / "sample.har"
        profiles_path = FIXTURES_DIR / "sample_repo_profiles.yaml"

        # 模拟预检：HAR 校验
        result = parse_har(har_path, profiles_path)
        assert len(result.endpoints) == 3
        assert result.summary.after_dedup == 3

        # 初始化 session
        state = init_session(tmp_path, str(har_path))
        assert state.current_wave == 0

        # 模拟 Wave 1 完成
        state = advance_wave(tmp_path, 1, data={
            "parsed": result.model_dump(),
        })
        assert state.waves["1"].status == WaveStatus.COMPLETED

    @pytest.mark.parametrize("start_wave,expected", [
        (3, "out of order"),
        (4, "out of order"),
    ])
    def test_wave_order_enforcement(
        self, tmp_path: Path, start_wave: int, expected: str
    ) -> None:
        """非当前波次的 advance 应被拒绝。"""
        init_session(tmp_path, "test.har")
        with pytest.raises(ValueError, match=expected):
            advance_wave(tmp_path, start_wave)
