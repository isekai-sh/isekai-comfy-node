"""
Cloud LLM API client utilities for Isekai ComfyUI Custom Nodes

Provides shared functionality for OpenAI, Claude, and Gemini API integrations.
"""

import os
import time
import requests
from typing import Dict, Any, Optional


class CloudLLMError(Exception):
    """Base exception for cloud LLM provider errors"""
    pass


def get_api_key(env_var_name: str, api_key_input: str, provider_name: str) -> str:
    """
    Get API key with priority: environment variable > node input.

    Prints warnings to guide users toward secure practices.

    Args:
        env_var_name: Name of environment variable (e.g., "OPENAI_API_KEY")
        api_key_input: API key from node input field (optional)
        provider_name: Provider name for error messages (e.g., "OpenAI")

    Returns:
        API key string

    Raises:
        CloudLLMError: If no API key found in either location

    Priority:
        1. Environment variable (RECOMMENDED) ✅
        2. Node input (FALLBACK) ⚠️

    Example:
        >>> api_key = get_api_key("OPENAI_API_KEY", "", "OpenAI")
        [Isekai] Using API key from OPENAI_API_KEY environment variable
    """
    # Check environment variable first (more secure)
    env_key = os.environ.get(env_var_name, "").strip()

    if env_key:
        print(f"[Isekai] Using API key from {env_var_name} environment variable")
        return env_key

    # Fall back to node input with security warning
    if api_key_input and api_key_input.strip():
        print(f"[Isekai] ⚠️  WARNING: API key provided via node input.")
        print(f"[Isekai] For security, set {env_var_name} environment variable instead.")
        print(f"[Isekai] API keys in node inputs may be saved in workflow JSON files.")
        return api_key_input.strip()

    # No API key found - provide helpful error message
    raise CloudLLMError(
        f"No {provider_name} API key provided. Either:\n"
        f"1. Set {env_var_name} environment variable (recommended), or\n"
        f"2. Enter API key in the node's api_key field\n\n"
        f"Get your API key from:\n"
        f"  OpenAI: https://platform.openai.com/api-keys\n"
        f"  Claude: https://console.anthropic.com/settings/keys\n"
        f"  Gemini: https://aistudio.google.com/apikey"
    )


def make_llm_request(
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: int = 30,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Make HTTP POST request to LLM API with error handling and retries.

    Args:
        url: API endpoint URL
        headers: Request headers including authentication
        payload: Request body as dictionary
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum retry attempts for rate limits (default: 3)

    Returns:
        API response as dictionary

    Raises:
        CloudLLMError: If request fails after retries

    Example:
        >>> response = make_llm_request(
        ...     "https://api.openai.com/v1/chat/completions",
        ...     {"Authorization": "Bearer sk-..."},
        ...     {"model": "gpt-4o", "messages": [...]}
        ... )
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout
            )

            # Handle successful responses
            if response.status_code == 200:
                return response.json()

            # Handle various error status codes
            if response.status_code == 401:
                raise CloudLLMError(
                    "Authentication failed. Invalid API key.\n"
                    "Please check your API key is correct and active."
                )

            if response.status_code == 403:
                raise CloudLLMError(
                    "Access forbidden. Check your API key permissions or account status."
                )

            if response.status_code == 429:
                # Rate limit - implement exponential backoff
                retry_after = int(response.headers.get("retry-after", 2 ** attempt))
                if attempt < max_retries - 1:
                    print(f"[Isekai] Rate limit hit. Retrying in {retry_after}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_after)
                    continue
                else:
                    raise CloudLLMError(
                        "Rate limit exceeded. Please wait a moment and try again.\n"
                        "Consider upgrading your API plan if this persists."
                    )

            if response.status_code == 500:
                raise CloudLLMError(
                    f"API server error (500). The provider's servers may be experiencing issues.\n"
                    f"Please try again in a moment."
                )

            if response.status_code >= 400:
                # Try to extract error message from response
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "") or error_data.get("message", "")
                    if error_msg:
                        raise CloudLLMError(f"API error: {error_msg}")
                except Exception:
                    pass

                raise CloudLLMError(
                    f"API request failed with status {response.status_code}.\n"
                    f"Response: {response.text[:200]}"
                )

        except requests.exceptions.Timeout:
            last_error = CloudLLMError(
                f"Request timed out after {timeout} seconds.\n"
                f"The API may be slow or unresponsive. Try again or increase timeout."
            )
            if attempt < max_retries - 1:
                print(f"[Isekai] Request timed out. Retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                continue
            raise last_error

        except requests.exceptions.ConnectionError as e:
            last_error = CloudLLMError(
                f"Connection failed: Unable to reach API endpoint.\n"
                f"Check your internet connection and try again.\n"
                f"Error: {str(e)}"
            )
            if attempt < max_retries - 1:
                print(f"[Isekai] Connection failed. Retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)
                continue
            raise last_error

        except CloudLLMError:
            # Re-raise our custom errors without retry
            raise

        except Exception as e:
            raise CloudLLMError(f"Unexpected error during API request: {str(e)}")

    # Should not reach here, but just in case
    if last_error:
        raise last_error
    raise CloudLLMError("Request failed after maximum retries")
