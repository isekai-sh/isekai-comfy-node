"""
Isekai Tag Selector Node for ComfyUI

This module provides dictionary-style tag lookup functionality based on trigger words.
"""

from typing import Tuple, Dict, Any
import re


class IsekaiTagSelector:
    """
    Outputs preset tags based on a trigger word using dictionary-style matching.

    This node functions as a key-value lookup system where trigger words map
    to predefined tag sets. Useful for quickly applying consistent tag sets
    based on character names, styles, or other identifiers.

    Supports TOML/INI-style format with sections:
    [TriggerWord]
    tags, separated, by, commas

    Also supports legacy format: TriggerWord: tags, separated, by, commas

    Matching is case-insensitive for better usability.

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING",)
        RETURN_NAMES: Tuple containing ("selected_tags",)
        FUNCTION: "select_tags"
        CATEGORY: "Isekai"

    Example:
        Presets:
        "[Superman]
        movie, superhero, dc, comic, blue, red

        [Batman]
        dark, knight, gotham, rich, black"

        trigger_word = "superman"
        Output: "movie, superhero, dc, comic, blue, red"
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required and optional input specifications:
            - trigger_word: String to search for in presets (required)
            - presets: Multiline string with TOML/INI format sections (required)
            - default_value: Fallback value if trigger not found (optional)
        """
        return {
            "required": {
                "trigger_word": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "forceInput": True
                }),
                "presets": ("STRING", {
                    "default": "[Superman]\nmovie, superhero, dc, comic, blue, red\n\n[Batman]\ndark, knight, gotham, rich, black\n\n[Wonder Woman]\namazon, warrior, princess, tiara",
                    "multiline": True,
                    "placeholder": "[TriggerWord]\ntags, separated, by, commas"
                }),
            },
            "optional": {
                "default_value": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("selected_tags",)
    FUNCTION = "select_tags"
    CATEGORY = "Isekai"

    def select_tags(
        self,
        trigger_word: str,
        presets: str,
        default_value: str = ""
    ) -> Tuple[str]:
        """
        Select tags based on trigger word using dictionary lookup.

        Searches through preset definitions and returns the tags associated
        with the matching trigger. Supports both TOML/INI format ([Section])
        and legacy colon format (Key: value).

        Matching is case-insensitive and whitespace-tolerant.

        Args:
            trigger_word: String to search for in presets
            presets: Multiline string with TOML/INI sections or legacy colon format
            default_value: Fallback value if trigger not found (default: "")

        Returns:
            Tuple containing the matched tags or default_value.

        Example:
            >>> node = IsekaiTagSelector()
            >>> presets = "[Batman]\\ndark, knight\\n\\n[Superman]\\nhero, cape"
            >>> result = node.select_tags("batman", presets, "unknown")
            >>> result[0]
            'dark, knight'
        """
        # Clean and normalize the trigger word (lowercase, no leading/trailing spaces)
        search_key = trigger_word.strip().lower()

        if not search_key:
            print("[Isekai] No trigger word provided.")
            return (default_value,)

        # Parse the presets - try TOML/INI format first, then fall back to legacy format
        tags_dict = self._parse_presets(presets)

        # Look up the trigger word
        if search_key in tags_dict:
            result = tags_dict[search_key]
            print(f"[Isekai] Trigger '{trigger_word}' matched: '{result[:100]}{'...' if len(result) > 100 else ''}'")
            return (result,)

        # No match found, return default fallback
        print(f"[Isekai] Trigger '{trigger_word}' not found. Using default.")
        return (default_value,)

    def _parse_presets(self, presets: str) -> Dict[str, str]:
        """
        Parse preset definitions into a dictionary.

        Supports two formats:
        1. TOML/INI style:
           [TriggerWord]
           tags, here

        2. Legacy style:
           TriggerWord: tags, here

        Args:
            presets: Multiline string with preset definitions

        Returns:
            Dictionary mapping trigger words (lowercase) to tag strings
        """
        tags_dict = {}
        lines = presets.splitlines()

        # Try to detect format by looking for section headers
        has_sections = any(re.match(r'^\s*\[.+\]\s*$', line) for line in lines)

        if has_sections:
            # Parse TOML/INI format
            current_section = None

            for line in lines:
                line = line.strip()

                # Skip empty lines
                if not line:
                    continue

                # Check for section header [SectionName]
                section_match = re.match(r'^\[(.+)\]$', line)
                if section_match:
                    current_section = section_match.group(1).strip().lower()
                    continue

                # If we have a current section, this line is the tags
                if current_section:
                    # Accumulate tags for the section (in case of multi-line tags)
                    if current_section in tags_dict:
                        # Append to existing tags
                        tags_dict[current_section] += ", " + line
                    else:
                        tags_dict[current_section] = line
        else:
            # Parse legacy colon format: Key: value
            for line in lines:
                # Skip empty lines or lines without a colon separator
                if not line.strip() or ":" not in line:
                    continue

                # Split into key (trigger) and value (tags)
                # Use split with maxsplit=1 to handle colons in tag values
                key, value = line.split(":", 1)

                # Store with lowercase key
                tags_dict[key.strip().lower()] = value.strip()

        return tags_dict
