"""
Isekai Load Text Node for ComfyUI

This module provides functionality to load text from a file and output it as a string.
"""

from typing import Tuple, Dict, Any
from pathlib import Path
import os

try:
    import folder_paths
    FOLDER_PATHS_AVAILABLE = True
except ImportError:
    FOLDER_PATHS_AVAILABLE = False


class IsekaiLoadText:
    """
    Loads text from a file and outputs it as a string.

    This node reads a text file from the specified path and returns its contents
    as a string. Useful for loading prompts, character lists, or other text data
    from external files.

    Supports two input modes:
    1. Dropdown selection from ComfyUI/text_files/ directory
    2. Custom absolute path entry

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING",)
        RETURN_NAMES: Tuple containing ("text_content",)
        FUNCTION: "load_text"
        CATEGORY: "Isekai"

    Example:
        text_file: "characters.txt" (from dropdown)
        OR
        custom_path: "/path/to/prompts.txt" (absolute path)
        Output: Contents of the file as a string
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing optional input specifications:
            - text_file: Dropdown list of files from text_files directory
            - custom_path: Manual path entry for files outside the directory
        """
        # Get list of text files if folder_paths is available
        text_files = []
        if FOLDER_PATHS_AVAILABLE:
            try:
                # Register text_files folder if not already registered
                if "text_files" not in folder_paths.folder_names_and_paths:
                    text_files_dir = os.path.join(folder_paths.models_dir, "text_files")
                    os.makedirs(text_files_dir, exist_ok=True)
                    folder_paths.add_model_folder_path("text_files", text_files_dir)

                # Get list of text files
                text_files = folder_paths.get_filename_list("text_files")
            except Exception as e:
                print(f"[Isekai] Load Text: Error accessing text_files directory: {e}")
                text_files = []

        # Provide a placeholder if no files found
        if not text_files:
            text_files = ["(no files found - use custom path)"]

        return {
            "optional": {
                "text_file": (text_files, {
                    "default": text_files[0] if text_files else None
                }),
                "custom_path": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "Or enter absolute path (e.g., /path/to/file.txt)"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text_content",)
    FUNCTION = "load_text"
    CATEGORY = "Isekai/IO"

    def load_text(self, text_file: str = None, custom_path: str = "") -> Tuple[str]:
        """
        Load text from a file.

        Reads the contents of the specified file and returns it as a string.
        Prioritizes custom_path if provided, otherwise uses text_file from dropdown.
        Returns empty string if file doesn't exist or can't be read.

        Args:
            text_file: Filename from dropdown selection (optional)
            custom_path: Absolute path to text file (optional)

        Returns:
            Tuple containing the file contents as a string.
            Returns empty string if file can't be read.

        Example:
            >>> node = IsekaiLoadText()
            >>> result = node.load_text(text_file="prompts.txt")
            >>> isinstance(result[0], str)
            True
        """
        # Determine which path to use
        file_path = None

        # Priority 1: Custom path if provided
        if custom_path and custom_path.strip():
            file_path = custom_path.strip()
            print(f"[Isekai] Load Text: Using custom path: {file_path}")

        # Priority 2: Text file from dropdown
        elif text_file and text_file != "(no files found - use custom path)":
            if FOLDER_PATHS_AVAILABLE:
                try:
                    # Get full path from folder_paths
                    full_path = folder_paths.get_full_path("text_files", text_file)
                    if full_path:
                        file_path = full_path
                        print(f"[Isekai] Load Text: Using file from directory: {text_file}")
                    else:
                        print(f"[Isekai] Load Text: Could not resolve path for: {text_file}")
                        return ("",)
                except Exception as e:
                    print(f"[Isekai] Load Text: Error resolving file path: {e}")
                    return ("",)
            else:
                print("[Isekai] Load Text: folder_paths not available, cannot use dropdown selection")
                return ("",)

        # No valid input provided
        if not file_path:
            print("[Isekai] Load Text: No file selected. Choose from dropdown or enter custom path.")
            return ("",)

        # Convert to Path object for better path handling
        path = Path(file_path)

        # Check if file exists
        if not path.exists():
            print(f"[Isekai] Load Text: File not found: {file_path}")
            return ("",)

        # Check if it's a file (not a directory)
        if not path.is_file():
            print(f"[Isekai] Load Text: Path is not a file: {file_path}")
            return ("",)

        # Try to read the file
        try:
            # Try UTF-8 first
            content = path.read_text(encoding="utf-8")
            print(f"[Isekai] Load Text: Successfully loaded {len(content)} characters from {path.name}")
            return (content,)
        except UnicodeDecodeError:
            # Fallback to system default encoding
            try:
                content = path.read_text()
                print(f"[Isekai] Load Text: Successfully loaded {len(content)} characters from {path.name} (fallback encoding)")
                return (content,)
            except Exception as e:
                print(f"[Isekai] Load Text: Error reading file: {e}")
                return ("",)
        except Exception as e:
            print(f"[Isekai] Load Text: Error reading file: {e}")
            return ("",)
