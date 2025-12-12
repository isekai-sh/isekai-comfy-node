"""
Validation utilities for Isekai ComfyUI Custom Nodes
"""

import re
from typing import Tuple
from urllib.parse import urlparse


def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate Isekai API key format.

    The Isekai API key must follow the format: isk_[64 hexadecimal characters]

    Args:
        api_key: API key string to validate

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty string.

    Example:
        >>> validate_api_key("isk_" + "a" * 64)
        (True, "")
        >>> validate_api_key("invalid")
        (False, "Invalid API key format. Expected format: isk_[64 hex characters]")
    """
    if not api_key or not api_key.strip():
        return False, "API key is required. Get your API key from Isekai dashboard."

    if not re.match(r'^isk_[a-f0-9]{64}$', api_key):
        return False, "Invalid API key format. Expected format: isk_[64 hex characters]"

    return True, ""


def validate_title(title: str, max_length: int = 200) -> Tuple[bool, str, str]:
    """
    Validate and sanitize title string.

    Args:
        title: Title string to validate
        max_length: Maximum allowed length (default: 200)

    Returns:
        Tuple of (is_valid, sanitized_title, error_message).
        If valid, error_message is empty string.

    Example:
        >>> validate_title("My Image")
        (True, "My Image", "")
        >>> validate_title("")
        (False, "", "Title is required and cannot be empty")
    """
    if not title or not title.strip():
        return False, "", "Title is required and cannot be empty"

    sanitized = title.strip()

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        return True, sanitized, f"Title truncated from {len(title)} to {max_length} characters"

    return True, sanitized, ""


def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL format.

    Args:
        url: URL string to validate

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty string.

    Example:
        >>> validate_url("http://localhost:11434")
        (True, "")
        >>> validate_url("not-a-url")
        (False, "Invalid URL format")
    """
    if not url or not url.strip():
        return False, "URL is required"

    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL format. Must include scheme (http/https) and host"
        return True, ""
    except Exception:
        return False, "Invalid URL format"


def sanitize_filename(text: str, max_length: int = 100) -> str:
    """
    Sanitize text for use in filenames.

    Removes special characters and limits length to create a safe filename.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length (default: 100)

    Returns:
        Sanitized filename-safe string

    Example:
        >>> sanitize_filename("My Image! @#$")
        'My_Image'
        >>> sanitize_filename("a" * 150)
        'aaa...' (truncated to 100 chars)
    """
    safe_text = re.sub(r'[^a-zA-Z0-9_\-\s]', '', text)
    safe_text = safe_text.replace(' ', '_')
    safe_text = safe_text[:max_length]
    return safe_text
