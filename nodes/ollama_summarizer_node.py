"""
Isekai Ollama Summarizer Node for ComfyUI

This module provides functionality to generate short titles from prompts using
local Ollama LLM models.
"""

from typing import Any, Dict, Tuple

# Try relative imports first (production), fall back to absolute
try:
    from ..utils.ollama_client import generate_summary, get_available_models
except (ImportError, ValueError):
    from utils.ollama_client import generate_summary, get_available_models


class IsekaiOllamaSummarizer:
    """
    Generates short titles from prompts using a local Ollama LLM instance.

    This node connects to a local Ollama server and uses an LLM model to
    summarize long prompts into concise, catchy titles. Useful for generating
    meaningful titles for uploads or organizing generated images.

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING",)
        RETURN_NAMES: Tuple containing ("title_summary",)
        FUNCTION: "summarize"
        CATEGORY: "Isekai"

    Example:
        text_input = "a detailed portrait of a fierce warrior woman in golden armor..."
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
            Dictionary containing required input specifications:
            - text_input: Text to summarize (required, force input)
            - ollama_url: Ollama server URL (required)
            - model: Ollama model selection dropdown (required)
        """
        # Fetch available models from Ollama
        installed_models = get_available_models()

        return {
            "required": {
                "text_input": ("STRING", {
                    "default": "",
                    "forceInput": True,
                    "multiline": True
                }),
                "ollama_url": ("STRING", {
                    "default": "http://localhost:11434",
                    "multiline": False
                }),
                "model": (installed_models,),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("title_summary",)
    FUNCTION = "summarize"
    CATEGORY = "Isekai"

    def summarize(
        self,
        text_input: str,
        ollama_url: str,
        model: str
    ) -> Tuple[str]:
        """
        Generate a short title summary from input text using Ollama.

        Args:
            text_input: Text to summarize (typically a long prompt)
            ollama_url: Ollama server URL (default: "http://localhost:11434")
            model: Ollama model name to use for generation

        Returns:
            Tuple containing the generated title. Returns "Untitled" if input
            is empty, or error messages if generation fails.

        Example:
            >>> node = IsekaiOllamaSummarizer()
            >>> result = node.summarize("long detailed prompt", "http://localhost:11434", "llama3")
            >>> isinstance(result[0], str)
            True
        """
        # Handle empty input
        if not text_input or not text_input.strip():
            print("[Isekai] Ollama Summarizer: Input empty.")
            return ("Untitled",)

        # Generate summary using Ollama client
        print(f"[Isekai] Requesting summary from {model}...")

        result = generate_summary(
            text=text_input,
            model=model,
            base_url=ollama_url
        )

        # Check if generation was successful
        if not result["success"]:
            error_msg = result.get("error", "Unknown error")
            print(f"[Isekai] {error_msg}")
            return (result["text"],)

        # Success - return generated title
        generated_title = result["text"]
        print(f"[Isekai] Title generated: '{generated_title}'")

        return (generated_title,)
