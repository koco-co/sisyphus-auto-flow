"""Template resolution tests for the code generator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sisyphus_auto_flow.core.models.assertion import AssertionConfig, AssertionType
from sisyphus_auto_flow.core.models.request import RequestConfig
from sisyphus_auto_flow.core.models.test_case import TestScenario as ScenarioModel
from sisyphus_auto_flow.core.models.test_case import TestStep as StepModel
from sisyphus_auto_flow.generator.code_generator import CodeGenerator

if TYPE_CHECKING:
    from pathlib import Path


def _build_scenario() -> ScenarioModel:
    return ScenarioModel(
        name="smoke",
        description="Smoke scenario",
        module="assets",
        epic="数据资产",
        feature="Smoke",
        tags=["crud"],
        steps=[
            StepModel(
                name="ping",
                description="ping step",
                request=RequestConfig(method="GET", url="/health"),
                assertions=[
                    AssertionConfig(
                        type=AssertionType.STATUS_CODE,
                        target="status_code",
                        expected=200,
                    )
                ],
            )
        ],
    )


def test_default_template_locator_prefers_packaged_templates() -> None:
    """Default template lookup should resolve packaged templates instead of assuming repo-local .claude paths."""
    from sisyphus_auto_flow.generator.template_locator import TemplateLocator

    template_dir = TemplateLocator().resolve()

    assert template_dir.name == "templates"
    assert "src/sisyphus_auto_flow/generator/templates" in str(template_dir)


def test_code_generator_uses_packaged_templates_by_default(tmp_path: Path) -> None:
    """Default generation should render from packaged templates and use the stable BaseAPITest import path."""
    output = CodeGenerator().generate(_build_scenario(), tmp_path)

    generated = output.read_text(encoding="utf-8")
    assert "from sisyphus_auto_flow.core.base import BaseAPITest" in generated


def test_code_generator_honors_explicit_template_dir(tmp_path: Path) -> None:
    """An explicit template directory should override packaged template resolution."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "crud_scenario.py.j2").write_text(
        '"""custom template"""\nfrom sisyphus_auto_flow.core.base import BaseAPITest\n',
        encoding="utf-8",
    )

    output = CodeGenerator(template_dir=template_dir).generate(_build_scenario(), tmp_path / "out")

    assert output.read_text(encoding="utf-8").startswith('"""custom template"""')
