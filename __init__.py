"""
Isekai ComfyUI Custom Node
"""

from . import nodes

# Build node mappings dynamically based on what successfully imported
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Define all possible nodes and their display names
_NODE_DEFINITIONS = {
    "IsekaiUpload": ("IsekaiUploadNode", "Upload"),
    "IsekaiDynamicString": ("IsekaiDynamicString", "Dynamic String"),
    "IsekaiConcatenateString": ("IsekaiConcatenateString", "Concatenate String"),
    "IsekaiTagSelector": ("IsekaiTagSelector", "Tag Selector"),
    "IsekaiOllamaSummarizer": ("IsekaiOllamaSummarizer", "Ollama Summarizer"),
    "IsekaiRoundRobin": ("IsekaiRoundRobin", "Round Robin"),
    "IsekaiLoadText": ("IsekaiLoadText", "Load Text"),
    "IsekaiRandomLineFromFile": ("IsekaiRandomLineFromFile", "Random Line From File"),
    "IsekaiCompressAndSave": ("IsekaiCompressAndSave", "Compress and Save"),
}

# Register nodes that successfully imported
for node_key, (class_name, display_name) in _NODE_DEFINITIONS.items():
    node_class = getattr(nodes, class_name, None)
    if node_class is not None:
        NODE_CLASS_MAPPINGS[node_key] = node_class
        NODE_DISPLAY_NAME_MAPPINGS[node_key] = display_name

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
