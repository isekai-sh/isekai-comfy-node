"""
Isekai ComfyUI Custom Node
"""

import sys
import os

print("[Isekai] Loading __init__.py...")

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"[Isekai] current_dir: {current_dir}")

# Import nodes module
# Note: We use a try-except to handle both package imports and direct imports
try:
    print("[Isekai] Attempting relative import...")
    from . import nodes
    print("[Isekai] Relative import succeeded")
except ImportError as e:
    print(f"[Isekai] Relative import failed: {e}")
    print("[Isekai] Attempting absolute import...")
    # Fallback for direct execution
    import nodes
    print("[Isekai] Absolute import succeeded")

print(f"[Isekai] nodes module loaded, __all__ has {len(nodes.__all__)} items")

# Build node mappings dynamically based on what successfully imported
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Define all possible nodes and their display names
# Organized by category: Dataset -> Image -> IO -> LLMs -> Upload
_NODE_DEFINITIONS = {
    # Dataset nodes
    "IsekaiConcatenateString": ("IsekaiConcatenateString", "Concatenate String"),
    "IsekaiDynamicString": ("IsekaiDynamicString", "Dynamic String"),
    "IsekaiRoundRobin": ("IsekaiRoundRobin", "Round Robin"),
    "IsekaiTagSelector": ("IsekaiTagSelector", "Tag Selector"),
    # Image/Blend nodes
    "IsekaiBlend": ("IsekaiBlend", "Blend Images"),
    "IsekaiColorAdjust": ("IsekaiColorAdjust", "Color Adjust"),
    "IsekaiColorRamp": ("IsekaiColorRamp", "Color Ramp"),
    "IsekaiLevels": ("IsekaiLevels", "Levels"),
    "IsekaiSplitToning": ("IsekaiSplitToning", "Split Toning"),
    # Image/Effects nodes
    "IsekaiBlur": ("IsekaiBlur", "Blur"),
    "IsekaiChromaticAberration": ("IsekaiChromaticAberration", "Chromatic Aberration"),
    "IsekaiColorFilter": ("IsekaiColorFilter", "Color Filter"),
    "IsekaiEdgeEnhance": ("IsekaiEdgeEnhance", "Edge Enhance"),
    "IsekaiGlare": ("IsekaiGlare", "Glare"),
    "IsekaiGrain": ("IsekaiGrain", "Grain"),
    "IsekaiInvert": ("IsekaiInvert", "Invert"),
    "IsekaiPixelate": ("IsekaiPixelate", "Pixelate"),
    "IsekaiPosterize": ("IsekaiPosterize", "Posterize"),
    "IsekaiSharpen": ("IsekaiSharpen", "Sharpen"),
    "IsekaiVignette": ("IsekaiVignette", "Vignette"),
    # Image/Transform nodes
    "IsekaiCrop": ("IsekaiCrop", "Crop"),
    "IsekaiFlip": ("IsekaiFlip", "Flip"),
    "IsekaiRotate": ("IsekaiRotate", "Rotate"),
    "IsekaiScale": ("IsekaiScale", "Scale"),
    "IsekaiTransform": ("IsekaiTransform", "Transform"),
    "IsekaiTranslate": ("IsekaiTranslate", "Translate"),
    # IO nodes
    "IsekaiCompressAndSave": ("IsekaiCompressAndSave", "Compress and Save"),
    "IsekaiLoadText": ("IsekaiLoadText", "Load Text"),
    "IsekaiRandomLineFromFile": ("IsekaiRandomLineFromFile", "Random Line From File"),
    # LLMs nodes
    "IsekaiClaude": ("IsekaiClaude", "Claude"),
    "IsekaiGemini": ("IsekaiGemini", "Gemini"),
    "IsekaiOllamaSummarizer": ("IsekaiOllamaSummarizer", "Ollama"),
    "IsekaiOpenAI": ("IsekaiOpenAI", "OpenAI"),
    # Upload nodes
    "IsekaiS3Upload": ("IsekaiS3Upload", "Upload to S3"),
    "IsekaiUpload": ("IsekaiUploadNode", "Upload to Isekai"),
}

# Register nodes that successfully imported
print(f"[Isekai] Registering {len(_NODE_DEFINITIONS)} node definitions...")
for node_key, (class_name, display_name) in _NODE_DEFINITIONS.items():
    node_class = getattr(nodes, class_name, None)
    if node_class is not None:
        NODE_CLASS_MAPPINGS[node_key] = node_class
        NODE_DISPLAY_NAME_MAPPINGS[node_key] = display_name

print(f"[Isekai] ✓ Registered {len(NODE_CLASS_MAPPINGS)} nodes successfully!")
if len(NODE_CLASS_MAPPINGS) == 0:
    print(f"[Isekai] ✗✗✗ WARNING: No nodes were registered!")
    print(f"[Isekai] nodes.__all__ = {nodes.__all__}")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
