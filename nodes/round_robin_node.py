"""
Isekai Round Robin Node for ComfyUI

This module provides functionality to cycle through items in batch-completion
mode, ensuring equal distribution of generations per item using a round-robin
pattern.
"""

import hashlib
import time
import tempfile
from typing import Tuple, Dict, Any
from pathlib import Path

# Try to use ComfyUI's temp directory, fallback to system temp for testing
try:
    import folder_paths
    _TEMP_DIR = Path(folder_paths.get_temp_directory())
except (ImportError, AttributeError):
    _TEMP_DIR = Path(tempfile.gettempdir())

# File-based state directory for append-only log in ComfyUI/temp
_STATE_DIR = _TEMP_DIR / "isekai" / "round_robin"
_STATE_DIR.mkdir(parents=True, exist_ok=True)


class IsekaiRoundRobin:
    """
    Cycles through items in batch-completion mode using round-robin pattern.

    Unlike IsekaiDynamicString which randomly selects items, this node ensures
    each item receives exactly 'images_per_item' generations before moving to
    the next item. State is maintained in-memory and resets when ComfyUI
    restarts.

    Attributes:
        RETURN_TYPES: Tuple containing ("STRING", "STRING", "INT")
        RETURN_NAMES: Tuple containing ("selected_item", "progress_info", "batch_count_needed")
        FUNCTION: "cycle_items"
        CATEGORY: "Isekai"

    Example:
        Input text_list:
        "Alice
        Bob
        Charlie"

        images_per_item = 32

        Output:
        - batch_count_needed: 96 (always shows 3 × 32 = 96)
        - Execution 1: "Alice", "Alice: 1/32 | Total: 1/96", 96
        - Execution 32: "Alice", "Alice: 32/32 | Total: 32/96", 96
        - Execution 33: "Bob", "Bob: 1/32 | Total: 33/96", 96
        - Execution 96: "Charlie", "Charlie: 32/32 | Total: 96/96", 96
        - Execution 97: Cycles back to "Alice: 1/32 | Total: 1/96", 96
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required input specifications:
            - text_list: Multiline string with one item per line
            - images_per_item: Number of images to generate per item
            - unique_id: Hidden input providing node's unique ID
        """
        return {
            "required": {
                "text_list": ("STRING", {
                    "multiline": True,
                    "default": "Item A\nItem B\nItem C",
                    "placeholder": "Enter items (one per line)..."
                }),
                "images_per_item": ("INT", {
                    "default": 32,
                    "min": 1,
                    "max": 1000,
                    "step": 1
                }),
                "batch_id": ("STRING", {
                    "default": "default",
                    "placeholder": "Enter unique ID for this batch..."
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("selected_item", "progress_info", "batch_count_needed")
    FUNCTION = "cycle_items"
    CATEGORY = "Isekai/Batch"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        Tell ComfyUI to NOT cache this node's output.
        Return a unique value each time to force re-execution.
        This ensures each batch execution gets a different character.
        """
        import time
        return time.time()

    def cycle_items(
        self,
        text_list: str,
        images_per_item: int,
        batch_id: str = "default"
    ) -> Tuple[str, str, int]:
        """
        Cycle through items in batch-completion mode.

        Returns the current item and automatically advances to the next item
        after 'images_per_item' executions. State persists per batch_id.

        State is cleared automatically when ComfyUI restarts.

        Args:
            text_list: Multiline string with one item per line
            images_per_item: Number of images to generate per item (1-1000)
            batch_id: Unique identifier for this batch (user-provided)

        Returns:
            Tuple containing:
            - selected_item: Current item from the list (STRING)
            - progress_info: Progress string like "Item A: 15/32 | Total: 15/96" (STRING)
            - batch_count_needed: Total executions needed to complete all items (INT)

            Returns ("", "No items", 0) if text_list is empty.
        """
        # Sanitize batch_id for filename
        import re
        batch_id = re.sub(r'[^\w\-]', '_', batch_id) if batch_id else "default"
        # Parse item list
        items = [line.strip() for line in text_list.splitlines() if line.strip()]

        # Handle empty item list
        if not items:
            print("[Isekai] Warning: Round Robin text_list is empty.")
            return ("", "No items", 0)

        # Calculate total executions needed
        total_executions = len(items) * images_per_item

        # Simple append-only log file approach
        # Each execution reads last line, uses next index, appends new line
        # Log file is unique to this batch (batch_id)
        log_file = _STATE_DIR / f"{batch_id}.log"

        # First execution: print helpful info
        if not log_file.exists():
            print(f"[Isekai] Round Robin initialized with {len(items)} items")
            print(f"[Isekai] 💡 TIP: Set batch count to {total_executions} to complete all items")
            print(f"[Isekai] {len(items)} items × {images_per_item} images = {total_executions} total executions")
            print(f"[Isekai] Batch ID: {batch_id}")
            print(f"[Isekai] State cleared automatically on ComfyUI restart")

        # Read last line to get last index used
        current_index = 0
        current_count = 0
        stored_images_per_item = images_per_item

        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    # Last line format: "index,count,images_per_item"
                    last_line = lines[-1].strip()
                    if last_line:
                        parts = last_line.split(',')
                        if len(parts) >= 2:
                            current_index = int(parts[0])
                            current_count = int(parts[1])
                            # Check if images_per_item is stored (backward compatibility)
                            if len(parts) >= 3:
                                stored_images_per_item = int(parts[2])
                                # If images_per_item changed, reset and warn
                                if stored_images_per_item != images_per_item:
                                    print(f"[Isekai] Round Robin: images_per_item changed from {stored_images_per_item} to {images_per_item}")
                                    print(f"[Isekai] Resetting counter. Delete {log_file} to start fresh.")
                                    current_index = 0
                                    current_count = 0

        # Calculate next state
        next_count = current_count + 1
        next_index = current_index

        if next_count >= images_per_item:
            next_index = (current_index + 1) % len(items)
            next_count = 0

        # Append new state to log (include images_per_item for validation)
        with open(log_file, 'a') as f:
            f.write(f"{next_index},{next_count},{images_per_item}\n")

        # === USE CURRENT VALUES ===
        # Select item using the ORIGINAL current_index (before advancement)
        current_item = items[current_index]

        # Calculate display values (1-indexed for user display)
        display_count = current_count + 1  # Convert 0-indexed to 1-indexed
        global_count = (current_index * images_per_item) + display_count

        # Format progress info with both local and global progress
        progress_info = f"{current_item}: {display_count}/{images_per_item} | Total: {global_count}/{total_executions}"

        # Log current state
        print(f"[Isekai] Round Robin: {progress_info}")

        # Log when cycling back to first item (when next state wrapped to start)
        if next_index == 0 and next_count == 0:
            print(f"[Isekai] Round Robin: Completed all {len(items)} items, cycling back to start")

        return (current_item, progress_info, total_executions)
