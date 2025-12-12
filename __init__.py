"""
Isekai ComfyUI Custom Node
"""

from . import nodes

# Build node mappings dynamically based on what successfully imported
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Define all possible nodes and their display names
_NODE_DEFINITIONS = {
    "IsekaiUpload": ("IsekaiUploadNode", "Isekai Upload"),
    "IsekaiDynamicString": ("IsekaiDynamicString", "Isekai Dynamic String"),
    "IsekaiConcatenateString": ("IsekaiConcatenateString", "Isekai Concatenate String"),
    "IsekaiTagSelector": ("IsekaiTagSelector", "Isekai Tag Selector"),
    "IsekaiOllamaSummarizer": ("IsekaiOllamaSummarizer", "Isekai Ollama Summarizer"),
    "IsekaiRoundRobin": ("IsekaiRoundRobin", "Isekai Round Robin"),
    "IsekaiLoadText": ("IsekaiLoadText", "Isekai Load Text"),
}

# Register nodes that successfully imported
for node_key, (class_name, display_name) in _NODE_DEFINITIONS.items():
    node_class = getattr(nodes, class_name, None)
    if node_class is not None:
        NODE_CLASS_MAPPINGS[node_key] = node_class
        NODE_DISPLAY_NAME_MAPPINGS[node_key] = display_name

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
