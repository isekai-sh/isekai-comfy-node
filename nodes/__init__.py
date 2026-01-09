"""
Isekai ComfyUI Custom Nodes

This package contains all custom node implementations for the Isekai platform.
"""

import sys
import os
import importlib.util

# PRE-LOAD our utils.image_utils module BEFORE any node imports
# This prevents ComfyUI's utils module from shadowing ours
_root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_image_utils_path = os.path.join(_root_dir, 'utils', 'image_utils.py')

if os.path.exists(_image_utils_path):
    spec = importlib.util.spec_from_file_location("utils.image_utils", _image_utils_path)
    _image_utils_module = importlib.util.module_from_spec(spec)
    sys.modules['utils.image_utils'] = _image_utils_module
    spec.loader.exec_module(_image_utils_module)
    print(f"[Isekai nodes] ✓ Pre-loaded utils.image_utils from {_image_utils_path}")
else:
    print(f"[Isekai nodes] ✗ utils/image_utils.py not found at {_image_utils_path}")

# Import nodes with graceful fallback when dependencies
# like torch may not be available
__all__ = []

print("[Isekai nodes] Starting imports...")

# ============================================================================
# Dataset Nodes
# ============================================================================

try:
    from .concatenate_string_node import IsekaiConcatenateString
    __all__.append("IsekaiConcatenateString")
except ImportError as e:
    print(f"[Isekai nodes] ✗ Failed to import IsekaiConcatenateString: {e}")

try:
    from .dynamic_string_node import IsekaiDynamicString
    __all__.append("IsekaiDynamicString")
except ImportError:
    pass

try:
    from .round_robin_node import IsekaiRoundRobin
    __all__.append("IsekaiRoundRobin")
except ImportError:
    pass

try:
    from .tag_selector_node import IsekaiTagSelector
    __all__.append("IsekaiTagSelector")
except ImportError:
    pass

# ============================================================================
# Image Nodes - Blend
# ============================================================================

print("[Isekai nodes] Importing Image/Blend nodes...")
try:
    from .image.blend.blend_node import IsekaiBlend
    __all__.append("IsekaiBlend")
    print("[Isekai nodes] ✓ IsekaiBlend")
except ImportError as e:
    print(f"[Isekai nodes] ✗ IsekaiBlend failed: {e}")

try:
    from .image.blend.color_adjust_node import IsekaiColorAdjust
    __all__.append("IsekaiColorAdjust")
    print("[Isekai nodes] ✓ IsekaiColorAdjust")
except ImportError as e:
    print(f"[Isekai nodes] ✗ IsekaiColorAdjust failed: {e}")

try:
    from .image.blend.color_ramp_node import IsekaiColorRamp
    __all__.append("IsekaiColorRamp")
except ImportError:
    pass

try:
    from .image.blend.levels_node import IsekaiLevels
    __all__.append("IsekaiLevels")
except ImportError:
    pass

try:
    from .image.blend.split_toning_node import IsekaiSplitToning
    __all__.append("IsekaiSplitToning")
except ImportError:
    pass

# ============================================================================
# Image Nodes - Effects
# ============================================================================

try:
    from .image.effects.blur_node import IsekaiBlur
    __all__.append("IsekaiBlur")
except ImportError:
    pass

try:
    from .image.effects.chromatic_aberration_node import IsekaiChromaticAberration
    __all__.append("IsekaiChromaticAberration")
except ImportError:
    pass

try:
    from .image.effects.color_filter_node import IsekaiColorFilter
    __all__.append("IsekaiColorFilter")
except ImportError:
    pass

try:
    from .image.effects.edge_enhance_node import IsekaiEdgeEnhance
    __all__.append("IsekaiEdgeEnhance")
except ImportError:
    pass

try:
    from .image.effects.glare_node import IsekaiGlare
    __all__.append("IsekaiGlare")
except ImportError:
    pass

try:
    from .image.effects.grain_node import IsekaiGrain
    __all__.append("IsekaiGrain")
except ImportError:
    pass

try:
    from .image.effects.invert_node import IsekaiInvert
    __all__.append("IsekaiInvert")
except ImportError:
    pass

try:
    from .image.effects.pixelate_node import IsekaiPixelate
    __all__.append("IsekaiPixelate")
except ImportError:
    pass

try:
    from .image.effects.posterize_node import IsekaiPosterize
    __all__.append("IsekaiPosterize")
except ImportError:
    pass

try:
    from .image.effects.sharpen_node import IsekaiSharpen
    __all__.append("IsekaiSharpen")
except ImportError:
    pass

try:
    from .image.effects.vignette_node import IsekaiVignette
    __all__.append("IsekaiVignette")
except ImportError:
    pass

# ============================================================================
# Image Nodes - Transform
# ============================================================================

try:
    from .image.transform.crop_node import IsekaiCrop
    __all__.append("IsekaiCrop")
except ImportError:
    pass

try:
    from .image.transform.flip_node import IsekaiFlip
    __all__.append("IsekaiFlip")
except ImportError:
    pass

try:
    from .image.transform.rotate_node import IsekaiRotate
    __all__.append("IsekaiRotate")
except ImportError:
    pass

try:
    from .image.transform.scale_node import IsekaiScale
    __all__.append("IsekaiScale")
except ImportError:
    pass

try:
    from .image.transform.transform_node import IsekaiTransform
    __all__.append("IsekaiTransform")
except ImportError:
    pass

try:
    from .image.transform.translate_node import IsekaiTranslate
    __all__.append("IsekaiTranslate")
except ImportError:
    pass

# ============================================================================
# IO Nodes
# ============================================================================

try:
    from .compress_and_save_node import IsekaiCompressAndSave
    __all__.append("IsekaiCompressAndSave")
except ImportError:
    pass

try:
    from .load_text_node import IsekaiLoadText
    __all__.append("IsekaiLoadText")
except ImportError:
    pass

try:
    from .random_from_file_node import IsekaiRandomLineFromFile
    __all__.append("IsekaiRandomLineFromFile")
except ImportError:
    pass

# ============================================================================
# LLMs Nodes
# ============================================================================

try:
    from .claude_node import IsekaiClaude
    __all__.append("IsekaiClaude")
except ImportError:
    pass

try:
    from .gemini_node import IsekaiGemini
    __all__.append("IsekaiGemini")
except ImportError:
    pass

try:
    from .ollama_summarizer_node import IsekaiOllamaSummarizer
    __all__.append("IsekaiOllamaSummarizer")
except ImportError:
    pass

try:
    from .openai_node import IsekaiOpenAI
    __all__.append("IsekaiOpenAI")
except ImportError:
    pass

# ============================================================================
# Upload Nodes
# ============================================================================

try:
    from .s3_upload_node import IsekaiS3Upload
    __all__.append("IsekaiS3Upload")
except ImportError:
    pass

try:
    from .upload_node import IsekaiUploadNode
    __all__.append("IsekaiUploadNode")
except ImportError:
    pass

print(f"[Isekai nodes] ✓ Finished imports: {len(__all__)} nodes loaded")
