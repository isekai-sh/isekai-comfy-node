"""
Isekai Round Robin Node for ComfyUI

This module provides functionality to cycle through items in batch-completion
mode, ensuring equal distribution of generations per item using a round-robin
pattern.
"""

from typing import Tuple, Dict, Any

# Module-level state storage (session-scoped)
_round_robin_state = {}


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
            - reset_trigger: Boolean to manually reset the cycler state
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
                "reset_trigger": ("BOOLEAN", {
                    "default": False
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("selected_item", "progress_info", "batch_count_needed")
    FUNCTION = "cycle_items"
    CATEGORY = "Isekai"

    def cycle_items(
        self,
        text_list: str,
        images_per_item: int,
        reset_trigger: bool = False
    ) -> Tuple[str, str, int]:
        """
        Cycle through items in batch-completion mode.

        Returns the current item and automatically advances to the next item
        after 'images_per_item' executions. State persists across multiple
        node executions within a session.

        Args:
            text_list: Multiline string with one item per line
            images_per_item: Number of images to generate per item (1-1000)
            reset_trigger: Set to True to reset cycler to first item

        Returns:
            Tuple containing:
            - selected_item: Current item from the list (STRING)
            - progress_info: Progress string like "Item A: 15/32 | Total: 15/96" (STRING)
            - batch_count_needed: Total executions needed to complete all items (INT)

            Returns ("", "No items", 0) if text_list is empty.

        Example:
            >>> node = IsekaiRoundRobin()
            >>> # First call
            >>> result = node.cycle_items("Alice\\nBob", 2, False)
            >>> result[0]  # selected_item
            'Alice'
            >>> result[1]  # progress_info
            'Alice: 1/2 | Total: 1/4'
            >>> result[2]  # batch_count_needed
            4
            >>> # Second call
            >>> result = node.cycle_items("Alice\\nBob", 2, False)
            >>> result[1]
            'Alice: 2/2 | Total: 2/4'
            >>> # Third call (advances to Bob)
            >>> result = node.cycle_items("Alice\\nBob", 2, False)
            >>> result[0]
            'Bob'
        """
        # Generate unique state key based on text_list content
        # This allows different workflows with different item lists
        # to maintain separate state
        state_key = hash(text_list.strip())

        # Parse item list
        items = [line.strip() for line in text_list.splitlines() if line.strip()]

        # Handle empty item list
        if not items:
            print("[Isekai] Warning: Round Robin text_list is empty.")
            return ("", "No items", 0)

        # Calculate total executions needed
        total_executions = len(items) * images_per_item

        # Initialize or reset state
        if state_key not in _round_robin_state or reset_trigger:
            _round_robin_state[state_key] = {
                'current_index': 0,
                'current_count': 0,
                'items': items
            }
            print(f"[Isekai] Round Robin initialized/reset with {len(items)} items")
            print(f"[Isekai] 💡 TIP: Set batch count to {total_executions} to complete all items")
            print(f"[Isekai] {len(items)} items × {images_per_item} images = {total_executions} total executions")

        # Retrieve state
        state = _round_robin_state[state_key]

        # Handle item list changes (number of items changed)
        # Reset to beginning if the list changed
        if len(state['items']) != len(items):
            print("[Isekai] Round Robin: Item list changed, resetting cycler")
            state['current_index'] = 0
            state['current_count'] = 0
            state['items'] = items

        # Get current item
        current_index = state['current_index']
        current_count = state['current_count']

        # Ensure index is valid (wrap around if needed)
        if current_index >= len(items):
            current_index = 0
            state['current_index'] = 0

        current_item = items[current_index]

        # Increment counter (1-indexed for display)
        current_count += 1

        # Calculate global progress
        global_count = (current_index * images_per_item) + current_count

        # Format progress info with both local and global progress
        progress_info = f"{current_item}: {current_count}/{images_per_item} | Total: {global_count}/{total_executions}"

        # Log current state
        print(f"[Isekai] Round Robin: {progress_info}")

        # Check if we need to advance to next item
        if current_count >= images_per_item:
            # Move to next item
            state['current_index'] = (current_index + 1) % len(items)
            state['current_count'] = 0

            # Log when cycling back to first item
            if state['current_index'] == 0:
                print(f"[Isekai] Round Robin: Completed all {len(items)} items, cycling back to start")
        else:
            # Update count for next execution
            state['current_count'] = current_count

        return (current_item, progress_info, total_executions)
