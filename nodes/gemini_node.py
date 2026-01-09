"""
Isekai Gemini Node for ComfyUI

This module provides integration with Google's Gemini API.
Supports Gemini 2.5 Flash, Gemini 3, and other Google AI models.
"""

from typing import Any, Dict, Tuple

# Try relative imports first (production), fall back to absolute
try:
    from ..utils.cloud_llm_client import get_api_key, make_llm_request, CloudLLMError
except (ImportError, ValueError):
    from utils.cloud_llm_client import get_api_key, make_llm_request, CloudLLMError


class IsekaiGemini:
    """
    Google Gemini API node for ComfyUI.

    Connects to Google's Gemini API to generate text using Gemini models. Supports
    customizable prompts, system instructions, and various model parameters.

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING",)
        RETURN_NAMES: Tuple containing ("response",)
        FUNCTION: "generate"
        CATEGORY: "Isekai/LLMs"

    Example:
        prompt = "Explain quantum computing"
        system_prompt = "You are a helpful physics teacher"
        model = "gemini-2.5-flash"
        Output: Detailed explanation of quantum computing
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required and optional input specifications:
            - prompt: User prompt text (required)
            - model: Gemini model selection (required)
            - system_prompt: System instructions (optional)
            - api_key: Google API key (optional, uses env var if not provided)
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
                    "gemini-2.5-flash",
                    "gemini-3-pro-preview"
                ],),
            },
            "optional": {
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Optional: Instructions for how Gemini should respond"
                }),
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "⚠️ Use GOOGLE_API_KEY env var instead"
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
                    "max": 8192,
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
        Generate text using Google Gemini API.

        Args:
            prompt: User prompt text
            model: Gemini model name (e.g., "gemini-2.5-flash")
            system_prompt: Optional system instructions
            api_key: Google API key (optional, uses GOOGLE_API_KEY env var if empty)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
            max_tokens: Maximum output tokens (default: 1000)

        Returns:
            Tuple containing the generated response text

        Raises:
            CloudLLMError: If API key missing or request fails

        Example:
            >>> node = IsekaiGemini()
            >>> result = node.generate(
            ...     "Explain AI",
            ...     "gemini-2.5-flash",
            ...     system_prompt="Be concise"
            ... )
            >>> isinstance(result[0], str)
            True
        """
        try:
            # Handle empty input
            if not prompt or not prompt.strip():
                print("[Isekai] Gemini: Input prompt is empty.")
                return ("",)

            # Get API key with priority: env var > node input
            api_key = get_api_key("GOOGLE_API_KEY", api_key, "Gemini")

            # Build contents array in Gemini's format
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt.strip()
                    }]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }

            # Add system instruction if provided
            if system_prompt and system_prompt.strip():
                payload["systemInstruction"] = {
                    "parts": [{
                        "text": system_prompt.strip()
                    }]
                }
                print(f"[Isekai] Gemini: Generating with {model} (with system prompt)...")
            else:
                print(f"[Isekai] Gemini: Generating with {model}...")

            # Prepare request (Gemini uses different header format)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            headers = {
                "x-goog-api-key": api_key,  # Note: different from other providers
                "Content-Type": "application/json"
            }

            # Make API request
            response = make_llm_request(url, headers, payload, timeout=60)

            # Extract generated text from Gemini's response format
            generated_text = response["candidates"][0]["content"]["parts"][0]["text"]

            # Log success
            token_usage = response.get("usageMetadata", {})
            input_tokens = token_usage.get("promptTokenCount", 0)
            output_tokens = token_usage.get("candidatesTokenCount", 0)
            print(f"[Isekai] Gemini: Response generated ({output_tokens} tokens)")
            print(f"[Isekai] Gemini: Token usage - Input: {input_tokens}, Output: {output_tokens}")

            # Check finish reason
            finish_reason = response["candidates"][0].get("finishReason")
            if finish_reason == "MAX_TOKENS":
                print("[Isekai] Gemini: Warning - Response truncated due to max_tokens limit")
            elif finish_reason in ["SAFETY", "RECITATION"]:
                print(f"[Isekai] Gemini: Warning - Response filtered due to {finish_reason}")

            return (generated_text,)

        except CloudLLMError as e:
            print(f"[Isekai] Gemini Error: {str(e)}")
            return (f"Error: {str(e)}",)
        except KeyError as e:
            print(f"[Isekai] Gemini Response Parse Error: Missing key {str(e)}")
            print(f"[Isekai] This may indicate a content filter or API response format change")
            return (f"Error: Unable to parse response (key {str(e)} not found)",)
        except Exception as e:
            print(f"[Isekai] Gemini Unexpected Error: {str(e)}")
            return (f"Unexpected error: {str(e)}",)
