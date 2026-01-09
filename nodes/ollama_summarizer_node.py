"""
Isekai Ollama Node for ComfyUI

This module provides a general-purpose interface to local Ollama LLM models.
Use it for text generation, summarization, analysis, or any LLM task.
"""

from typing import Any, Dict, Tuple

# Try relative imports first (production), fall back to absolute
try:
    from ..utils.ollama_client import generate_text, get_available_models
except (ImportError, ValueError):
    from utils.ollama_client import generate_text, get_available_models


class IsekaiOllamaSummarizer:
    """
    General-purpose Ollama LLM node for text generation and processing.

    This node connects to a local Ollama server and uses an LLM model to
    process text based on your custom prompts. Supports any Ollama model
    and fully customizable system/user prompts.

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING",)
        RETURN_NAMES: Tuple containing ("response",)
        FUNCTION: "generate"
        CATEGORY: "Isekai/LLMs"

    Example:
        prompt = "a detailed portrait of a fierce warrior woman in golden armor..."
        system_prompt = "Summarize this into a short title"
        model = "llama3"
        Output: "Warrior in Golden Armor"
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Fetches available Ollama models dynamically at import time to populate
        the model selection dropdown.

        Returns:
            Dictionary containing required and optional input specifications:
            - prompt: Main text input to process (required)
            - model: Ollama model selection dropdown (required)
            - system_prompt: Instructions for the LLM (optional)
            - ollama_url: Ollama server URL (optional)
        """
        # Fetch available models from Ollama
        installed_models = get_available_models()

        return {
            "required": {
                "prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Enter your prompt here..."
                }),
                "model": (installed_models,),
            },
            "optional": {
                "system_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Optional: Instructions for how the LLM should process the prompt"
                }),
                "ollama_url": ("STRING", {
                    "default": "http://localhost:11434",
                    "multiline": False,
                    "placeholder": "http://localhost:11434"
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
        ollama_url: str = "http://localhost:11434"
    ) -> Tuple[str]:
        """
        Generate text using Ollama LLM based on the provided prompt.

        Args:
            prompt: Main text input to process
            model: Ollama model name to use for generation
            system_prompt: Optional instructions for the LLM (e.g., "Summarize this", "Translate to French")
            ollama_url: Ollama server URL (default: "http://localhost:11434")

        Returns:
            Tuple containing the generated response. Returns error messages if generation fails.

        Example:
            >>> node = IsekaiOllamaSummarizer()
            >>> result = node.generate("long prompt", "llama3", "Summarize this")
            >>> isinstance(result[0], str)
            True
        """
        # Handle empty input
        if not prompt or not prompt.strip():
            print("[Isekai] Ollama: Input prompt is empty.")
            return ("",)

        # Log the request
        if system_prompt and system_prompt.strip():
            print(f"[Isekai] Ollama: Generating with {model} (with system prompt)...")
        else:
            print(f"[Isekai] Ollama: Generating with {model}...")

        # Generate text using Ollama client
        result = generate_text(
            text=prompt,
            model=model,
            base_url=ollama_url,
            system_prompt=system_prompt if system_prompt and system_prompt.strip() else None
        )

        # Check if generation was successful
        if not result["success"]:
            error_msg = result.get("error", "Unknown error")
            print(f"[Isekai] Ollama Error: {error_msg}")
            return (result["text"],)

        # Success - return generated response
        generated_response = result["text"]
        print(f"[Isekai] Ollama: Response generated ({len(generated_response)} characters)")

        return (generated_response,)
