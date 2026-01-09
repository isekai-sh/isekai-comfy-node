"""
Isekai Concatenate String Node for ComfyUI

This module provides functionality to join multiple string inputs with a configurable delimiter.
"""

from typing import Tuple, Dict, Any, Optional


class IsekaiConcatenateString:
    """
    Joins multiple string inputs with a configurable delimiter.

    This node accepts up to 10 optional string inputs (text_a through text_j)
    and concatenates them using the specified delimiter. Only non-empty inputs
    are included in the concatenation.

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING",)
        RETURN_NAMES: Tuple containing ("concatenated_string",)
        FUNCTION: "concatenate"
        CATEGORY: "Isekai"

    Example:
        text_a = "portrait"
        text_b = "of a warrior"
        text_c = "in armor"
        delimiter = " "
        Output: "portrait of a warrior in armor"
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required and optional input specifications:
            - delimiter: String to use between joined texts (required)
            - text_a through text_j: Optional string inputs (forceInput=True)
        """
        return {
            "required": {
                "delimiter": ("STRING", {
                    "default": " ",
                    "multiline": False
                }),
            },
            "optional": {
                "text_a": ("STRING", {"forceInput": True, "multiline": True}),
                "text_b": ("STRING", {"forceInput": True, "multiline": True}),
                "text_c": ("STRING", {"forceInput": True, "multiline": True}),
                "text_d": ("STRING", {"forceInput": True, "multiline": True}),
                "text_e": ("STRING", {"forceInput": True, "multiline": True}),
                "text_f": ("STRING", {"forceInput": True, "multiline": True}),
                "text_g": ("STRING", {"forceInput": True, "multiline": True}),
                "text_h": ("STRING", {"forceInput": True, "multiline": True}),
                "text_i": ("STRING", {"forceInput": True, "multiline": True}),
                "text_j": ("STRING", {"forceInput": True, "multiline": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("concatenated_string",)
    FUNCTION = "concatenate"
    CATEGORY = "Isekai/Dataset"

    def concatenate(
        self,
        delimiter: str = " ",
        text_a: Optional[str] = None,
        text_b: Optional[str] = None,
        text_c: Optional[str] = None,
        text_d: Optional[str] = None,
        text_e: Optional[str] = None,
        text_f: Optional[str] = None,
        text_g: Optional[str] = None,
        text_h: Optional[str] = None,
        text_i: Optional[str] = None,
        text_j: Optional[str] = None
    ) -> Tuple[str]:
        """
        Concatenate multiple string inputs with delimiter.

        The function uses **kwargs internally to handle variable inputs.
        Inputs are processed in alphabetical order (text_a, text_b, etc.)
        and only non-empty values are included in the concatenation.

        Args:
            delimiter: String to use between joined texts (default: " ")
            text_a: First optional text input
            text_b: Second optional text input
            text_c: Third optional text input
            text_d: Fourth optional text input
            text_e: Fifth optional text input
            text_f: Sixth optional text input
            text_g: Seventh optional text input
            text_h: Eighth optional text input
            text_i: Ninth optional text input
            text_j: Tenth optional text input

        Returns:
            Tuple containing concatenated string. Returns empty string if
            no inputs are provided.

        Example:
            >>> node = IsekaiConcatenateString()
            >>> result = node.concatenate(" ", text_a="hello", text_b="world")
            >>> result[0]
            'hello world'
        """
        # Collect all keyword arguments
        kwargs = {
            'text_a': text_a,
            'text_b': text_b,
            'text_c': text_c,
            'text_d': text_d,
            'text_e': text_e,
            'text_f': text_f,
            'text_g': text_g,
            'text_h': text_h,
            'text_i': text_i,
            'text_j': text_j
        }

        # Sort keys alphabetically to ensure consistent ordering (A before B before C, etc.)
        sorted_keys = sorted(kwargs.keys())

        valid_texts = []

        for key in sorted_keys:
            # Only process keys that start with "text_"
            if key.startswith("text_"):
                value = kwargs[key]
                # Only add if the value is not None and not empty
                if value:
                    valid_texts.append(value)

        # Return empty string if no valid inputs
        if not valid_texts:
            return ("",)

        # Join with delimiter
        result = delimiter.join(valid_texts)
        print(f"[Isekai] Concatenated {len(valid_texts)} inputs: '{result[:100]}{'...' if len(result) > 100 else ''}'")

        return (result,)
