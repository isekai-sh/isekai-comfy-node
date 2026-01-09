"""
Isekai OpenAI Node for ComfyUI

This module provides integration with OpenAI's Chat Completions API.
Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.
"""

from typing import Any, Dict, Tuple

# Try relative imports first (production), fall back to absolute
try:
    from ..utils.cloud_llm_client import get_api_key, make_llm_request, CloudLLMError
except (ImportError, ValueError):
    from utils.cloud_llm_client import get_api_key, make_llm_request, CloudLLMError


class IsekaiOpenAI:
    """
    OpenAI Chat Completions API node for ComfyUI.

    Connects to OpenAI's API to generate text using GPT models. Supports
    customizable prompts, system instructions, and various model parameters.

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING",)
        RETURN_NAMES: Tuple containing ("response",)
        FUNCTION: "generate"
        CATEGORY: "Isekai/LLMs"

    Example:
        prompt = "Explain quantum computing"
        system_prompt = "You are a helpful physics teacher"
        model = "gpt-4o"
        Output: Detailed explanation of quantum computing
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required and optional input specifications:
            - prompt: User prompt text (required)
            - model: OpenAI model selection (required)
            - system_prompt: System instructions (optional)
            - api_key: OpenAI API key (optional, uses env var if not provided)
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
                    "gpt-4o",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo",
                    "gpt-4o-mini"
                ],),
            },
            "optional": {
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Optional: Instructions for how the AI should respond"
                }),
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "⚠️ Use OPENAI_API_KEY env var instead"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "display": "slider"
                }),
                "max_tokens": ("INT", {
                    "default": 1000,
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
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Tuple[str]:
        """
        Generate text using OpenAI Chat Completions API.

        Args:
            prompt: User prompt text
            model: OpenAI model name (e.g., "gpt-4o")
            system_prompt: Optional system instructions
            api_key: OpenAI API key (optional, uses OPENAI_API_KEY env var if empty)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
            max_tokens: Maximum output tokens (default: 1000)

        Returns:
            Tuple containing the generated response text

        Raises:
            CloudLLMError: If API key missing or request fails

        Example:
            >>> node = IsekaiOpenAI()
            >>> result = node.generate(
            ...     "Explain AI",
            ...     "gpt-4o",
            ...     system_prompt="Be concise"
            ... )
            >>> isinstance(result[0], str)
            True
        """
        try:
            # Handle empty input
            if not prompt or not prompt.strip():
                print("[Isekai] OpenAI: Input prompt is empty.")
                return ("",)

            # Get API key with priority: env var > node input
            api_key = get_api_key("OPENAI_API_KEY", api_key, "OpenAI")

            # Build messages array
            messages = []

            # Add system prompt if provided
            if system_prompt and system_prompt.strip():
                messages.append({
                    "role": "system",
                    "content": system_prompt.strip()
                })
                print(f"[Isekai] OpenAI: Generating with {model} (with system prompt)...")
            else:
                print(f"[Isekai] OpenAI: Generating with {model}...")

            # Add user prompt
            messages.append({
                "role": "user",
                "content": prompt.strip()
            })

            # Prepare request
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # Make API request
            response = make_llm_request(url, headers, payload, timeout=60)

            # Extract generated text
            generated_text = response["choices"][0]["message"]["content"]

            # Log success
            token_usage = response.get("usage", {})
            input_tokens = token_usage.get("prompt_tokens", 0)
            output_tokens = token_usage.get("completion_tokens", 0)
            print(f"[Isekai] OpenAI: Response generated ({output_tokens} tokens)")
            print(f"[Isekai] OpenAI: Token usage - Input: {input_tokens}, Output: {output_tokens}")

            return (generated_text,)

        except CloudLLMError as e:
            print(f"[Isekai] OpenAI Error: {str(e)}")
            return (f"Error: {str(e)}",)
        except Exception as e:
            print(f"[Isekai] OpenAI Unexpected Error: {str(e)}")
            return (f"Unexpected error: {str(e)}",)
