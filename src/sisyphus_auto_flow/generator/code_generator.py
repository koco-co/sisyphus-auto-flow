"""代码生成器。

基于 Jinja2 模板和 TestScenario 数据模型，
生成标准化的 pytest 测试用例文件。
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader
from loguru import logger

if TYPE_CHECKING:
    from sisyphus_auto_flow.harness.models.test_case import TestScenario


class CodeGenerator:
    """测试用例代码生成器。"""

    def __init__(self, template_dir: str | Path | None = None) -> None:
        if template_dir is None:
            project_root = Path(__file__).resolve().parents[3]
            template_dir = project_root / ".claude" / "skills" / "har-to-testcase" / "references"

        self._template_dir = Path(template_dir)
        if self._template_dir.exists():
            self._env = Environment(
                loader=FileSystemLoader(str(self._template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
                keep_trailing_newline=True,
            )
        else:
            self._env = None
            logger.warning(f"模板目录不存在: {self._template_dir}")

    def generate(self, scenario: TestScenario, output_dir: str | Path) -> Path:
        """根据场景生成测试用例文件。"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"test_{scenario.module}_{scenario.name}.py"
        filepath = output_path / filename

        template_name = self._select_template(scenario)

        if self._env and template_name:
            template = self._env.get_template(template_name)
            code = template.render(scenario=scenario)
        else:
            code = self._generate_fallback(scenario)

        filepath.write_text(code, encoding="utf-8")
        logger.info(f"用例已生成: {filepath}")
        return filepath

    def _select_template(self, scenario: TestScenario) -> str | None:
        if not self._env:
            return None
        tags = {t.lower() for t in scenario.tags}
        if "crud" in tags:
            return "crud_scenario.py.j2"
        if "auth" in tags:
            return "auth_scenario.py.j2"
        if "negative" in tags or "error" in tags:
            return "negative_scenario.py.j2"
        return "crud_scenario.py.j2"

    def _generate_fallback(self, scenario: TestScenario) -> str:
        """当模板不可用时，直接生成代码。"""
        lines = [
            f'"""{scenario.description or scenario.name} 测试。"""',
            "",
            "import allure",
            "",
            "from sisyphus_auto_flow.harness.base_test import BaseAPITest",
            "",
            "",
            f'@allure.epic("{scenario.epic or scenario.module}")',
            f'@allure.feature("{scenario.feature or scenario.name}")',
            f"class Test{scenario.module.title().replace('_', '')}{scenario.name.title().replace('_', '')}(BaseAPITest):",
            f'    """{scenario.description or scenario.name}。"""',
            "",
        ]

        for i, step in enumerate(scenario.steps, start=1):
            lines.extend(
                [
                    f'    @allure.story("{step.name}")',
                    "    @allure.severity(allure.severity_level.NORMAL)",
                    f"    def test_{i:02d}_{step.name}(self):",
                    f'        """{step.description or step.name}。"""',
                    f'        response = self.request("{step.request.method}", "{step.request.url}")',
                    f"        self.assert_status(response, {step.assertions[0].expected if step.assertions else 200})",
                    "",
                ]
            )

        return "\n".join(lines) + "\n"
