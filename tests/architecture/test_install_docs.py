"""Install and onboarding documentation tests."""

from __future__ import annotations

from pathlib import Path


def test_install_guide_covers_macos_windows_and_ai_setup_hint() -> None:
    """Install.md and README should guide both OS setup and AI-assisted onboarding."""
    repo_root = Path(__file__).resolve().parents[2]
    install_doc = repo_root / "Install.md"
    readme = repo_root / "README.md"

    assert install_doc.exists()
    install_text = install_doc.read_text(encoding="utf-8")
    assert "macOS" in install_text
    assert "Windows" in install_text
    assert "uv" in install_text

    readme_text = readme.read_text(encoding="utf-8")
    assert "Install.md" in readme_text
    assert (
        "按照 https://github.com/koco-co/sisyphus-auto-flow/blob/main/Install.md把它的本地开发环境初始化好"
        in readme_text
    )
