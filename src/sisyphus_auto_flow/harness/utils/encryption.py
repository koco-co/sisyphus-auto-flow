"""加解密工具。

提供测试数据的脱敏和简单加解密功能。
用于处理敏感配置和测试数据保护。
"""

from __future__ import annotations

import base64
import secrets
import string
from typing import Any


def encrypt_value(value: str, key: str = "sisyphus") -> str:
    """使用 XOR + Base64 进行轻量级加密。

    仅用于测试数据保护，非安全级加密。

    Args:
        value: 待加密的明文
        key: 加密密钥

    Returns:
        Base64 编码的密文
    """
    key_bytes = key.encode("utf-8")
    value_bytes = value.encode("utf-8")
    encrypted = bytes(v ^ key_bytes[i % len(key_bytes)] for i, v in enumerate(value_bytes))
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_value(encrypted: str, key: str = "sisyphus") -> str:
    """解密 XOR + Base64 加密的密文。

    Args:
        encrypted: Base64 编码的密文
        key: 解密密钥（须与加密时一致）

    Returns:
        解密后的明文
    """
    key_bytes = key.encode("utf-8")
    encrypted_bytes = base64.b64decode(encrypted.encode("utf-8"))
    decrypted = bytes(v ^ key_bytes[i % len(key_bytes)] for i, v in enumerate(encrypted_bytes))
    return decrypted.decode("utf-8")


def mask_sensitive(data: dict[str, Any], fields: set[str] | None = None) -> dict[str, Any]:
    """对敏感字段进行脱敏处理。

    Args:
        data: 原始数据字典
        fields: 需要脱敏的字段名集合（小写匹配）

    Returns:
        脱敏后的字典（浅拷贝）
    """
    default_fields = {"password", "token", "secret", "authorization", "cookie", "api_key", "access_token"}
    target_fields = fields or default_fields

    result = dict(data)
    for key in result:
        if key.lower() in target_fields:
            result[key] = "***"
    return result


def generate_test_password(length: int = 12) -> str:
    """生成随机测试密码。

    包含大小写字母和数字。

    Args:
        length: 密码长度，默认 12

    Returns:
        随机密码字符串
    """
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def encode_base64(value: str) -> str:
    """Base64 编码。"""
    return base64.b64encode(value.encode("utf-8")).decode("utf-8")


def decode_base64(encoded: str) -> str:
    """Base64 解码。"""
    return base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
