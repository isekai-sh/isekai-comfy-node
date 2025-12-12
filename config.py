"""
Configuration management for Isekai ComfyUI custom node
"""
import os

DEFAULT_API_URL = "https://api.isekai.sh"


def get_api_url():
    """
    Get Isekai API URL from environment or use default

    Environment variable: ISEKAI_API_URL
    Default: https://api.isekai.sh

    For local development, set:
    export ISEKAI_API_URL=http://localhost:4000
    """
    return os.environ.get("ISEKAI_API_URL", DEFAULT_API_URL)
