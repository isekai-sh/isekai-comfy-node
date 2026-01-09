"""
Isekai Dynamic String Node for ComfyUI

This module provides functionality to randomly select a line from multiline text
with reproducible results using a seed value.
"""

import random
from typing import Tuple, Dict, Any


class IsekaiDynamicString:
    """
    Randomly selects one line from multiline text input.

    This node takes a multiline string and selects one line randomly based on
    a seed value, allowing for reproducible random selection. Useful for
    varying prompts in batch generations while maintaining deterministic results.

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING",)
        RETURN_NAMES: Tuple containing ("selected_string",)
        FUNCTION: "pick_random_line"
        CATEGORY: "Isekai"

    Example:
        Input text_list:
        "portrait of a warrior
        landscape with mountains
        abstract digital art"

        Seed: 42
        Output: One of the three lines (deterministic for same seed)
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required input specifications:
            - text_list: Multiline string with one option per line
            - seed: Integer seed for reproducible random selection
        """
        return {
            "required": {
                "text_list": ("STRING", {
                    "multiline": True,
                    "default": "ducks\ndogs\ncats\nwhales",
                    "placeholder": "Enter items separated by new lines..."
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("selected_string",)
    FUNCTION = "pick_random_line"
    CATEGORY = "Isekai/Dataset"

    def pick_random_line(self, text_list: str, seed: int) -> Tuple[str]:
        """
        Select a random line from multiline text using seed.

        The same seed will always return the same line, allowing for
        reproducible results across multiple executions.

        Args:
            text_list: Multiline string with one option per line
            seed: Integer seed for random number generator

        Returns:
            Tuple containing the selected line as a string.
            Returns empty string if no valid lines are found.

        Example:
            >>> node = IsekaiDynamicString()
            >>> result = node.pick_random_line("line1\\nline2\\nline3", 42)
            >>> isinstance(result[0], str)
            True
            >>> len(result[0]) > 0
            True
        """
        # Set random seed for deterministic selection
        random.seed(seed)

        # Split into lines and filter out empty lines
        lines = text_list.splitlines()
        valid_lines = [line.strip() for line in lines if line.strip()]

        # Handle empty input
        if not valid_lines:
            print("[Isekai] Warning: Dynamic String input list is empty.")
            return ("",)

        # Select random line
        choice = random.choice(valid_lines)
        print(f"[Isekai] Dynamic String selected: '{choice}'")

        return (choice,)
