# code-style-python 模块索引

> 由 tide/SKILL.md 按需读取，根据 convention-fingerprint.yaml 决定加载哪些模块。

## 加载规则

| 条件 | 加载模块 |
|------|---------|
| 始终 | `00-core.md` |
| fingerprint.api.type == "enum" | `10-api-enum.md` |
| fingerprint.api.type == "class" | `10-api-class.md` |
| fingerprint.api.type in ("inline", null) | `10-api-inline.md` |
| fingerprint.http_client.client_pattern == "custom_class" | `20-client-custom.md` |
| fingerprint.http_client.library == "httpx" | `20-client-httpx.md` |
| fingerprint.http_client.library == "requests" | `20-client-requests.md` |
| fingerprint.assertion.style == "code_success" | `30-assert-code-success.md` |
| fingerprint.assertion.style in ("status_only", null) | `30-assert-status-only.md` |
| fingerprint.test_style.file_suffix == "*_test.py" | `40-test-structure-dtstack.md` |
| 以上都不匹配 | `40-test-structure-standard.md` |
