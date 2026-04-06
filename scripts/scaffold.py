"""Scaffold generator — creates a new project directory from Jinja2 templates."""
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_CLIENT_PY = '''\
"""HTTP client — immutable wrapper around httpx."""
from dataclasses import dataclass, field
import httpx

@dataclass(frozen=True)
class APIClient:
    base_url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0

    def _build_client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, headers=self.headers, timeout=self.timeout)

    def get(self, path: str, **kwargs) -> httpx.Response:
        with self._build_client() as c:
            return c.get(path, **kwargs)

    def post(self, path: str, **kwargs) -> httpx.Response:
        with self._build_client() as c:
            return c.post(path, **kwargs)

    def put(self, path: str, **kwargs) -> httpx.Response:
        with self._build_client() as c:
            return c.put(path, **kwargs)

    def delete(self, path: str, **kwargs) -> httpx.Response:
        with self._build_client() as c:
            return c.delete(path, **kwargs)
'''

_ASSERTIONS_PY = '''\
"""L1-L5 assertion helpers."""
import httpx

def assert_protocol(  # noqa: E501
    response: httpx.Response,
    *,
    expected_status: int = 200,
    max_time_ms: int = 5000,
    expected_content_type: str = "application/json",
) -> None:
    assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}"
    elapsed_ms = response.elapsed.total_seconds() * 1000
    assert elapsed_ms <= max_time_ms, f"Response too slow: {elapsed_ms:.0f}ms > {max_time_ms}ms"
    content_type = response.headers.get("content-type", "")
    assert expected_content_type in content_type, f"Content-Type mismatch: {content_type}"
'''

_DB_PY = '''\
"""Database query helper — read-only, for assertion verification."""
from dataclasses import dataclass
import pymysql
from urllib.parse import urlparse

@dataclass(frozen=True)
class DBHelper:
    url: str

    def _connect(self):
        parsed = urlparse(self.url)
        return pymysql.connect(  # noqa: E501
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip("/"),
            cursorclass=pymysql.cursors.DictCursor,
        )

    def query_one(self, sql: str, params: tuple = ()) -> dict | None:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchone()
        finally:
            conn.close()

    def query_all(self, sql: str, params: tuple = ()) -> list[dict]:
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()
        finally:
            conn.close()

    def count(self, table: str, where: str = "1=1", params: tuple = ()) -> int:
        result = self.query_one(f"SELECT COUNT(*) as cnt FROM {table} WHERE {where}", params)
        return result["cnt"] if result else 0
'''

_GITIGNORE = """\
__pycache__/
*.py[cod]
.venv/
.autoflow/
.repos/
.trash/
.env
htmlcov/
reports/
.pytest_cache/
*.egg-info/
dist/
"""

_MAKEFILE = """\
.PHONY: test-all test-interface test-scenario test-unit report lint typecheck

test-all:
\tuv run pytest tests/ -v

test-interface:
\tuv run pytest tests/interface/ -v -m interface

test-scenario:
\tuv run pytest tests/scenariotest/ -v -m scenario

test-unit:
\tuv run pytest tests/unittest/ -v -m unit

report:
\tuv run pytest tests/ --alluredir=reports/allure-results
\tallure serve reports/allure-results

lint:
\tuv run ruff check .
\tuv run ruff format --check .

typecheck:
\tuv run pyright .
"""


@dataclass(frozen=True)
class ScaffoldConfig:
    project_root: Path
    project_name: str
    base_url: str
    db_configured: bool = False


def _write_if_not_exists(path: Path, content: str) -> bool:
    """Write content to path only if the file does not already exist.

    Returns True if the file was written, False if it already existed.
    """
    if path.exists():
        return False
    path.write_text(content)
    return True


def generate_project(config: ScaffoldConfig) -> list[str]:
    """Generate a scaffold project from templates.

    Returns a list of file paths (relative to project_root) that were created.
    """
    root = config.project_root
    created: list[str] = []

    # 1. Create directories
    dirs = [
        "tests/interface",
        "tests/scenariotest",
        "tests/unittest",
        "core/models",
        ".autoflow",
        ".repos",
        ".trash",
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

    # 2. Render Jinja2 templates
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), keep_trailing_newline=True)
    template_vars = {
        "project_name": config.project_name,
        "base_url": config.base_url,
        "db_configured": config.db_configured,
    }

    pyproject_content = env.get_template("pyproject.toml.j2").render(**template_vars)
    if _write_if_not_exists(root / "pyproject.toml", pyproject_content):
        created.append("pyproject.toml")

    conftest_content = env.get_template("conftest.py.j2").render(**template_vars)
    if _write_if_not_exists(root / "tests" / "conftest.py", conftest_content):
        created.append("tests/conftest.py")

    # 3. Copy .env.example as-is
    env_example_src = TEMPLATES_DIR / ".env.example"
    env_example_dst = root / ".env.example"
    if _write_if_not_exists(env_example_dst, env_example_src.read_text()):
        created.append(".env.example")

    # 4. Static __init__.py files
    init_files = [
        "core/__init__.py",
        "core/models/__init__.py",
        "tests/interface/__init__.py",
        "tests/scenariotest/__init__.py",
        "tests/unittest/__init__.py",
    ]
    for rel in init_files:
        if _write_if_not_exists(root / rel, ""):
            created.append(rel)

    # 5. core/client.py
    if _write_if_not_exists(root / "core" / "client.py", _CLIENT_PY):
        created.append("core/client.py")

    # 6. core/assertions.py
    if _write_if_not_exists(root / "core" / "assertions.py", _ASSERTIONS_PY):
        created.append("core/assertions.py")

    # 7. core/db.py (only when db_configured)
    if config.db_configured and _write_if_not_exists(root / "core" / "db.py", _DB_PY):
        created.append("core/db.py")

    # 8. .gitignore
    if _write_if_not_exists(root / ".gitignore", _GITIGNORE):
        created.append(".gitignore")

    # 9. Makefile
    if _write_if_not_exists(root / "Makefile", _MAKEFILE):
        created.append("Makefile")

    return created
