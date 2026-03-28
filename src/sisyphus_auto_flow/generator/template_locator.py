"""模板定位器。"""

from __future__ import annotations

from pathlib import Path


class TemplateLocator:
    """解析代码生成模板目录。"""

    def __init__(self, template_dir: str | Path | None = None) -> None:
        self._template_dir = Path(template_dir) if template_dir is not None else None

    def resolve(self) -> Path:
        """返回模板目录。

        优先级：
        1. 显式传入的 template_dir
        2. 包内模板目录 `src/sisyphus_auto_flow/generator/templates`
        3. 兼容性回退到 repo-local `.claude/skills/har-to-testcase/references`
        """
        if self._template_dir is not None:
            return self._template_dir

        package_templates = Path(__file__).resolve().with_name("templates")
        if package_templates.exists():
            return package_templates

        project_root = Path(__file__).resolve().parents[3]
        return project_root / ".claude" / "skills" / "har-to-testcase" / "references"
