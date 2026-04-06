"""HAR parser: transforms raw HAR JSON into structured ParsedResult.

Pipeline: load → filter_entries → dedup_entries → match_repo → build ParsedResult
"""

from __future__ import annotations

import base64
import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Sensitive headers stripped from parsed output
# ---------------------------------------------------------------------------
_SENSITIVE_HEADERS = frozenset({"cookie", "authorization", "x-auth-token"})

# ---------------------------------------------------------------------------
# Static extensions to drop
# ---------------------------------------------------------------------------
_STATIC_EXTS = frozenset(
    {".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
     ".woff", ".woff2", ".ttf", ".map"}
)

# ---------------------------------------------------------------------------
# Noise URL patterns to drop (substring match)
# ---------------------------------------------------------------------------
_NOISE_PATTERNS = ("hot-update", "sockjs", "__webpack", "source-map")


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class HarHeader(BaseModel):
    name: str
    value: str


class HarRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    method: str
    url: str
    headers: list[HarHeader] = []
    post_data: dict | None = Field(default=None, alias="postData")

    # ---- computed properties ----

    @property
    def body(self) -> dict | None:
        """Parse post_data.text as JSON; return None if absent or non-JSON."""
        if self.post_data is None:
            return None
        text = self.post_data.get("text")
        if not text:
            return None
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None

    @property
    def path(self) -> str:
        """URL path component."""
        return urlparse(self.url).path

    @property
    def content_type(self) -> str | None:
        """Value of the Content-Type request header (lowercase)."""
        for h in self.headers:
            if h.name.lower() == "content-type":
                return h.value.lower()
        return None


class HarContent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mime_type: str = Field(default="", alias="mimeType")
    text: str | None = None
    encoding: str | None = None


class HarResponse(BaseModel):
    status: int
    headers: list[HarHeader] = []
    content: HarContent = HarContent()

    # ---- computed properties ----

    @property
    def body(self) -> dict | None:
        """Parse content.text as JSON, handling optional base64 encoding."""
        text = self.content.text
        if not text:
            return None
        if self.content.encoding == "base64":
            try:
                text = base64.b64decode(text).decode()
            except Exception:
                return None
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None

    @property
    def content_type(self) -> str | None:
        """Value of the Content-Type response header (lowercase)."""
        for h in self.headers:
            if h.name.lower() == "content-type":
                return h.value.lower()
        # Fall back to mime_type field
        if self.content.mime_type:
            return self.content.mime_type.lower()
        return None


class HarEntry(BaseModel):
    time: float = 0.0
    request: HarRequest
    response: HarResponse

    @model_validator(mode="before")
    @classmethod
    def _coerce_fields(cls, data: dict) -> dict:
        """Accept raw HAR dicts that contain extra fields (cache, timings, etc.)."""
        return data


# ---------------------------------------------------------------------------
# Parsed output models
# ---------------------------------------------------------------------------


class ParsedEndpoint(BaseModel):
    id: str
    method: str
    path: str
    service: str
    module: str
    request: dict
    response: dict
    matched_repo: str | None
    matched_branch: str | None


class ParsedSummary(BaseModel):
    total_raw: int
    after_filter: int
    after_dedup: int
    services: list[str]
    modules: list[str]


class ParsedResult(BaseModel):
    source_har: str
    parsed_at: str
    base_url: str
    endpoints: list[ParsedEndpoint]
    summary: ParsedSummary


# ---------------------------------------------------------------------------
# filter_entries
# ---------------------------------------------------------------------------


def filter_entries(entries: list[HarEntry]) -> list[HarEntry]:
    """Drop static resources, WebSocket upgrades, noise patterns, and non-JSON responses."""
    result: list[HarEntry] = []
    for entry in entries:
        path = entry.request.path

        # Drop WebSocket (status 101)
        if entry.response.status == 101:
            continue

        # Drop static file extensions
        path_lower = path.lower()
        suffix = Path(path_lower).suffix
        if suffix in _STATIC_EXTS:
            continue

        # Drop noise patterns
        if any(pattern in path_lower for pattern in _NOISE_PATTERNS):
            continue

        # Keep only application/json responses
        ct = entry.response.content_type or ""
        if "application/json" not in ct:
            continue

        result.append(entry)
    return result


# ---------------------------------------------------------------------------
# dedup_entries
# ---------------------------------------------------------------------------


def _body_hash(body: dict | None) -> str:
    if body is None:
        return "null"
    return hashlib.md5(
        json.dumps(body, sort_keys=True).encode(), usedforsecurity=False
    ).hexdigest()


def dedup_entries(entries: list[HarEntry]) -> list[HarEntry]:
    """Deduplicate by (method, path, status, body_hash); first occurrence wins."""
    seen: set[str] = set()
    result: list[HarEntry] = []
    for entry in entries:
        key = ":".join([
            entry.request.method,
            entry.request.path,
            str(entry.response.status),
            _body_hash(entry.request.body),
        ])
        if key not in seen:
            seen.add(key)
            result.append(entry)
    return result


# ---------------------------------------------------------------------------
# match_repo
# ---------------------------------------------------------------------------


def match_repo(
    path: str, profiles: list[dict]
) -> tuple[str | None, str | None]:
    """Match *path* against url_prefixes in profiles; return (name, branch) or (None, None)."""
    for profile in profiles:
        for prefix in profile.get("url_prefixes", []):
            if path.startswith(prefix):
                return profile["name"], profile["branch"]
    return None, None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_service_module(path: str) -> tuple[str, str]:
    """Derive (service, module) from URL path parts.

    Example: /dassets/v1/datamap/recentQuery → service=dassets, module=datamap
    """
    parts = [p for p in path.split("/") if p]
    service = parts[0] if len(parts) > 0 else ""
    module = parts[2] if len(parts) > 2 else (parts[1] if len(parts) > 1 else "")
    return service, module


def _strip_sensitive_headers(headers: list[HarHeader]) -> list[dict]:
    return [
        {"name": h.name, "value": h.value}
        for h in headers
        if h.name.lower() not in _SENSITIVE_HEADERS
    ]


def _extract_base_url(entry: HarEntry) -> str:
    parsed = urlparse(entry.request.url)
    return f"{parsed.scheme}://{parsed.netloc}"


# ---------------------------------------------------------------------------
# parse_har
# ---------------------------------------------------------------------------


def parse_har(
    har_path: Path,
    profiles_path: Path | None,
) -> ParsedResult:
    """Load, validate, filter, dedup, and enrich HAR entries into a ParsedResult."""
    # --- Load ---
    try:
        raw = json.loads(har_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Invalid HAR: {exc}") from exc

    if "log" not in raw or "entries" not in raw.get("log", {}):
        raise ValueError("Invalid HAR: missing log.entries")

    raw_entries = raw["log"]["entries"]

    if not raw_entries:
        raise ValueError("No entries found in HAR")

    entries = [HarEntry(**e) for e in raw_entries]
    total_raw = len(entries)

    # --- Load profiles ---
    profiles: list[dict] = []
    if profiles_path is not None:
        try:
            profiles_data = yaml.safe_load(profiles_path.read_text())
            profiles = profiles_data.get("profiles", [])
        except Exception:
            profiles = []

    # --- Filter & dedup ---
    filtered = filter_entries(entries)
    after_filter = len(filtered)

    deduped = dedup_entries(filtered)
    after_dedup = len(deduped)

    # --- Build base_url ---
    base_url = _extract_base_url(entries[0])

    # --- Build endpoints ---
    endpoints: list[ParsedEndpoint] = []
    services: set[str] = set()
    modules: set[str] = set()

    for entry in deduped:
        path = entry.request.path
        service, module = _extract_service_module(path)
        matched_repo, matched_branch = match_repo(path, profiles)

        services.add(service)
        modules.add(module)

        endpoints.append(
            ParsedEndpoint(
                id=str(uuid.uuid4()),
                method=entry.request.method,
                path=path,
                service=service,
                module=module,
                request={
                    "headers": _strip_sensitive_headers(entry.request.headers),
                    "body": entry.request.body,
                },
                response={
                    "status": entry.response.status,
                    "body": entry.response.body,
                    "time_ms": entry.time,
                },
                matched_repo=matched_repo,
                matched_branch=matched_branch,
            )
        )

    return ParsedResult(
        source_har=str(har_path),
        parsed_at=datetime.now(tz=UTC).isoformat(),
        base_url=base_url,
        endpoints=endpoints,
        summary=ParsedSummary(
            total_raw=total_raw,
            after_filter=after_filter,
            after_dedup=after_dedup,
            services=sorted(services),
            modules=sorted(modules),
        ),
    )
