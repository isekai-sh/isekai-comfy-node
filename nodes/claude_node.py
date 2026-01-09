"""
Isekai Claude Node for ComfyUI

This module provides integration with Anthropic's Claude Messages API.
Supports Claude Opus, Sonnet, and Haiku models.
"""

from typing import Any, Dict, Tuple

# Try relative imports first (production), fall back to absolute
try:
    from ..utils.cloud_llm_client import get_api_key, make_llm_request, CloudLLMError
except (ImportError, ValueError):
    from utils.cloud_llm_client import get_api_key, make_llm_request, CloudLLMError


class IsekaiClaude:
    """
    Anthropic Claude Messages API node for ComfyUI.

    Connects to Anthropic's API to generate text using Claude models. Supports
    customizable prompts, system instructions, and various model parameters.

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING",)
        RETURN_NAMES: Tuple containing ("response",)
        FUNCTION: "generate"
        CATEGORY: "Isekai/LLMs"

    Example:
        prompt = "Explain quantum computing"
        system_prompt = "You are a helpful physics teacher"
        model = "claude-sonnet-4-5"
        Output: Detailed explanation of quantum computing
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required and optional input specifications:
            - prompt: User prompt text (required)
            - model: Claude model selection (required)
            - system_prompt: System instructions (optional)
            - api_key: Anthropic API key (optional, uses env var if not provided)
            - temperature: Sampling temperature (optional)
            - max_tokens: Maximum output tokens (optional)
        """
        return {
            "required": {
                "prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Enter your prompt here..."
                }),
                "model": ([
                    "claude-sonnet-4-5",
                    "claude-opus-4-5",
                    "claude-3-5-haiku-latest"
                ],),
            },
            "optional": {
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Optional: Instructions for how Claude should respond"
                }),
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "⚠️ Use ANTHROPIC_API_KEY env var instead"
                }),
                "temperature": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "display": "slider"
                }),
                "max_tokens": ("INT", {
                    "default": 1024,
                    "min": 1,
                    "max": 4096,
                    "step": 1
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "generate"
    CATEGORY = "Isekai/LLMs"

    def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: str = "",
        api_key: str = "",
        temperature: float = 1.0,
        max_tokens: int = 1024
    ) -> Tuple[str]:
        """
        Generate text using Anthropic Claude Messages API.

        Args:
            prompt: User prompt text
            model: Claude model name (e.g., "claude-sonnet-4-5")
            system_prompt: Optional system instructions
            api_key: Anthropic API key (optional, uses ANTHROPIC_API_KEY env var if empty)
            temperature: Sampling temperature 0.0-1.0 (default: 1.0)
            max_tokens: Maximum output tokens (default: 1024)

        Returns:
            Tuple containing the generated response text

        Raises:
            CloudLLMError: If API key missing or request fails

        Example:
            >>> node = IsekaiClaude()
            >>> result = node.generate(
            ...     "Explain AI",
            ...     "claude-sonnet-4-5",
            ...     system_prompt="Be concise"
            ... )
            >>> isinstance(result[0], str)
            True
        """
        try:
            # Handle empty input
            if not prompt or not prompt.strip():
                print("[Isekai] Claude: Input prompt is empty.")
                return ("",)

            # Get API key with priority: env var > node input
            api_key = get_api_key("ANTHROPIC_API_KEY", api_key, "Claude")

            # Build messages array (user message only)
            messages = [{
                "role": "user",
                "content": prompt.strip()
            }]

            # Prepare request payload
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature
            }

            # Add system prompt if provided (separate field for Claude)
            if system_prompt and system_prompt.strip():
                payload["system"] = system_prompt.strip()
                print(f"[Isekai] Claude: Generating with {model} (with system prompt)...")
            else:
                print(f"[Isekai] Claude: Generating with {model}...")

            # Prepare request headers (Claude requires specific headers)
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "X-Api-Key": api_key,
                "anthropic-version": "2023-06-01",  # Required by Claude API
                "Content-Type": "application/json"
            }

            # Make API request
            response = make_llm_request(url, headers, payload, timeout=60)

            # Extract generated text from Claude's response format
            generated_text = response["content"][0]["text"]

            # Log success
            token_usage = response.get("usage", {})
            input_tokens = token_usage.get("input_tokens", 0)
            output_tokens = token_usage.get("output_tokens", 0)
            print(f"[Isekai] Claude: Response generated ({output_tokens} tokens)")
            print(f"[Isekai] Claude: Token usage - Input: {input_tokens}, Output: {output_tokens}")

            # Check stop reason
            stop_reason = response.get("stop_reason")
            if stop_reason == "max_tokens":
                print("[Isekai] Claude: Warning - Response truncated due to max_tokens limit")

            return (generated_text,)

        except CloudLLMError as e:
            print(f"[Isekai] Claude Error: {str(e)}")
            return (f"Error: {str(e)}",)
        except Exception as e:
            print(f"[Isekai] Claude Unexpected Error: {str(e)}")
            return (f"Unexpected error: {str(e)}",)
