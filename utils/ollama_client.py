"""
Ollama API client utilities for Isekai ComfyUI Custom Nodes
"""

import json

import requests
from typing import List, Optional, Dict, Any


OLLAMA_RESPONSE_MODE_GENERAL = "General"
OLLAMA_RESPONSE_MODE_SHORT = "Short response"
OLLAMA_RESPONSE_MODE_OPTIONS = [
    OLLAMA_RESPONSE_MODE_GENERAL,
    OLLAMA_RESPONSE_MODE_SHORT,
]


def get_available_models(
    base_url: str = "http://localhost:11434",
    timeout: int = 1
) -> List[str]:
    """
    Fetch the list of available models from a local Ollama instance.

    Args:
        base_url: Ollama server URL (default: "http://localhost:11434")
        timeout: Request timeout in seconds (default: 1)

    Returns:
        List of available model names. Returns default fallback models if
        Ollama is not running or connection fails.

    Example:
        >>> models = get_available_models()
        >>> isinstance(models, list)
        True
        >>> len(models) > 0
        True
    """
    default_models = ["llama3", "mistral", "llama2", "clip", "llava"]
    url = f"{base_url.rstrip('/')}/api/tags"

    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            if models:
                return models
    except Exception:
        pass

    return default_models


def generate_text(
    text: str,
    model: str,
    base_url: str = "http://localhost:11434",
    system_prompt: Optional[str] = None,
    timeout: int = 120,
    response_mode: str = OLLAMA_RESPONSE_MODE_GENERAL,
) -> Dict[str, Any]:
    """
    Generate text using Ollama LLM.

    Args:
        text: Main prompt text to process
        model: Ollama model name to use
        base_url: Ollama server URL (default: "http://localhost:11434")
        system_prompt: Optional system prompt to guide generation (instructions for the LLM)
        timeout: Request timeout in seconds (default: 120)
        response_mode: ``General`` preserves Ollama's normal generation
            behavior. ``Short response`` opts into deterministic structured
            output tuned for short titles and similar one-line responses.

    Returns:
        Dictionary containing:
        - success (bool): Whether the request succeeded
        - text (str): Generated text or error message
        - error (Optional[str]): Error message if failed

    Example:
        >>> result = generate_text("Long prompt text", "llama3")
        >>> "text" in result and "success" in result
        True
    """
    if not text or not text.strip():
        return {
            "success": False,
            "text": "",
            "error": "Input text is empty"
        }

    url = f"{base_url.rstrip('/')}/api/generate"

    # Build the full prompt with optional system prompt
    if system_prompt and system_prompt.strip():
        full_prompt = f"{system_prompt}\n\n{text}"
    else:
        full_prompt = text

    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
    }
    short_response = response_mode == OLLAMA_RESPONSE_MODE_SHORT
    if short_response:
        response_schema = {
            "type": "object",
            "properties": {"response": {"type": "string"}},
            "required": ["response"],
            "additionalProperties": False,
        }
        payload.update({
            "format": response_schema,
            # Reasoning can consume thousands of invisible tokens for a title.
            "think": False,
            "keep_alive": "10m",
            "options": {
                "temperature": 0,
                "seed": 0,
                "num_ctx": 16384,
                "num_predict": 64,
            },
        })

    try:
        response = requests.post(url, json=payload, timeout=timeout)

        if response.status_code != 200:
            return {
                "success": False,
                "text": f"Error: {response.status_code}",
                "error": f"Ollama API returned status code {response.status_code}"
            }

        result = response.json()
        raw_output = result.get("response", "")
        if short_response and not raw_output:
            # Qwen3-VL may put structured output in ``thinking`` despite
            # receiving think=false. Limit this compatibility path to the
            # explicitly structured short-response mode.
            raw_output = result.get("thinking", "")
        generated_text = raw_output.strip() if isinstance(raw_output, str) else ""
        if short_response and generated_text:
            try:
                structured_output = json.loads(generated_text)
            except (TypeError, json.JSONDecodeError):
                structured_output = None
            if isinstance(structured_output, dict):
                generated_text = str(structured_output.get("response", "")).strip()

        # Clean up generated text
        generated_text = generated_text.replace('"', '').replace("'", "").replace("\n", " ")

        if not generated_text:
            return {
                "success": False,
                "text": "Error: Empty response",
                "error": "Ollama returned empty response"
            }

        return {
            "success": True,
            "text": generated_text,
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "text": "Connection Timeout",
            "error": f"Request to Ollama at {base_url} timed out after {timeout} seconds"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "text": "Connection Failed",
            "error": f"Failed to connect to Ollama at {base_url}. Ensure Ollama is running."
        }
    except Exception as e:
        return {
            "success": False,
            "text": "Error",
            "error": f"Unexpected error: {str(e)}"
        }
