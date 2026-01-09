"""
Isekai Random From File Node for ComfyUI

This module provides functionality to load a text file and return a random line
using seed-based deterministic selection.
"""

import random
import os
from typing import Tuple, Dict, Any
from pathlib import Path

try:
    import folder_paths
    FOLDER_PATHS_AVAILABLE = True
except ImportError:
    FOLDER_PATHS_AVAILABLE = False


class IsekaiRandomLineFromFile:
    """
    Loads text file from models/text_files/ and returns a random line.

    This node takes a filename (without .txt extension), loads the file from
    the text_files directory, and returns a randomly selected line using
    seed-based deterministic selection. Useful for varying prompts or content
    in batch generations while maintaining reproducible results.

    Supports automatic .txt extension appending - input "String" loads "String.txt".

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING",)
        RETURN_NAMES: Tuple containing ("random_line",)
        FUNCTION: "get_random_line"
        CATEGORY: "Isekai"

    Example:
        file_name: "String"
        seed: 42
        Output: One line from String.txt (deterministic for same seed)
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required input specifications:
            - file_name: String filename without .txt extension
            - seed: Integer seed for reproducible random selection
        """
        return {
            "required": {
                "file_name": ("STRING", {
                    "default": "String",
                    "multiline": False,
                    "placeholder": "Enter filename (without .txt)"
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("random_line",)
    FUNCTION = "get_random_line"
    CATEGORY = "Isekai/Text"

    def get_random_line(self, file_name: str, seed: int) -> Tuple[str]:
        """
        Load text file and return a random line using seed.

        The same seed will always return the same line from the same file,
        allowing for reproducible results across multiple executions.

        Args:
            file_name: Filename without .txt extension (e.g., "Naruto")
            seed: Integer seed for random number generator

        Returns:
            Tuple containing the selected line as a string.
            Returns empty string if file not found or no valid lines.

        Example:
            >>> node = IsekaiRandomLineFromFile()
            >>> result = node.get_random_line("String", 42)
            >>> isinstance(result[0], str)
            True
        """
        # Check if folder_paths is available
        if not FOLDER_PATHS_AVAILABLE:
            print("[Isekai] Random From File: folder_paths not available, cannot load file")
            return ("",)

        # Validate input
        if not file_name or not file_name.strip():
            print("[Isekai] Random From File: No filename provided")
            return ("",)

        file_name = file_name.strip()

        # Append .txt extension if not already present
        if not file_name.lower().endswith('.txt'):
            filename = f"{file_name}.txt"
        else:
            filename = file_name

        # Get full path using folder_paths
        try:
            file_path = folder_paths.get_full_path("text_files", filename)
            if not file_path:
                print(f"[Isekai] Random From File: Could not resolve path for: {filename}")
                return ("",)
        except Exception as e:
            print(f"[Isekai] Random From File: Error resolving file path: {e}")
            return ("",)

        # Convert to Path object for better path handling
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            print(f"[Isekai] Random From File: File not found: {filename}")
            return ("",)

        # Check if it's a file (not a directory)
        if not path.is_file():
            print(f"[Isekai] Random From File: Path is not a file: {filename}")
            return ("",)

        # Try to read the file
        try:
            # Try UTF-8 first
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Fallback to system default encoding
            try:
                content = path.read_text()
                print(f"[Isekai] Random From File: Loaded {filename} with fallback encoding")
            except Exception as e:
                print(f"[Isekai] Random From File: Error reading file: {e}")
                return ("",)
        except Exception as e:
            print(f"[Isekai] Random From File: Error reading file: {e}")
            return ("",)

        # Split into lines and filter out empty lines
        lines = content.splitlines()
        valid_lines = [line.strip() for line in lines if line.strip()]

        # Handle empty file
        if not valid_lines:
            print(f"[Isekai] Random From File: No valid lines found in {filename}")
            return ("",)

        # Set random seed for deterministic selection
        random.seed(seed)

        # Select random line
        selected_line = random.choice(valid_lines)
        print(f"[Isekai] Random From File: Selected line from {filename} ({len(valid_lines)} total lines)")

        return (selected_line,)
