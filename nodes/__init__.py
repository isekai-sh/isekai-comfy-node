"""
Isekai ComfyUI Custom Nodes

This package contains all custom node implementations for the Isekai platform.
"""

# Import nodes with graceful fallback when dependencies
# like torch may not be available
__all__ = []

try:
    from .upload_node import IsekaiUploadNode
    __all__.append("IsekaiUploadNode")
except ImportError:
    pass

try:
    from .dynamic_string_node import IsekaiDynamicString
    __all__.append("IsekaiDynamicString")
except ImportError:
    pass

try:
    from .concatenate_string_node import IsekaiConcatenateString
    __all__.append("IsekaiConcatenateString")
except ImportError:
    pass

try:
    from .tag_selector_node import IsekaiTagSelector
    __all__.append("IsekaiTagSelector")
except ImportError:
    pass

try:
    from .ollama_summarizer_node import IsekaiOllamaSummarizer
    __all__.append("IsekaiOllamaSummarizer")
except ImportError:
    pass

try:
    from .round_robin_node import IsekaiRoundRobin
    __all__.append("IsekaiRoundRobin")
except ImportError:
    pass

try:
    from .load_text_node import IsekaiLoadText
    __all__.append("IsekaiLoadText")
except ImportError:
    pass

try:
    from .compress_image_node import IsekaiCompressImage
    __all__.append("IsekaiCompressImage")
except ImportError:
    pass
