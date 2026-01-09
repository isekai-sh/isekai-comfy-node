#!/usr/bin/env python3
"""
Debug script to check which nodes are successfully loading.
Run this from the ComfyUI custom_nodes directory with ComfyUI's Python environment.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("ISEKAI NODE LOADING DEBUG")
print("=" * 80)

# Try to import the main module
try:
    import __init__ as isekai_nodes
    print("✓ Main __init__.py imported successfully\n")
except Exception as e:
    print(f"✗ Failed to import __init__.py: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check NODE_CLASS_MAPPINGS
if hasattr(isekai_nodes, 'NODE_CLASS_MAPPINGS'):
    mappings = isekai_nodes.NODE_CLASS_MAPPINGS
    print(f"Total nodes registered: {len(mappings)}")
    print("\nRegistered nodes by category:\n")

    categories = {
        'Dataset': [],
        'Image/Blend': [],
        'Image/Effects': [],
        'Image/Transform': [],
        'IO': [],
        'LLMs': [],
        'Upload': []
    }

    for key in sorted(mappings.keys()):
        if 'String' in key or 'RoundRobin' in key or 'TagSelector' in key:
            categories['Dataset'].append(key)
        elif 'Blend' in key or 'ColorAdjust' in key or 'ColorRamp' in key or 'Levels' in key or 'SplitToning' in key:
            categories['Image/Blend'].append(key)
        elif 'Blur' in key or 'Sharpen' in key or 'Color' in key or 'Invert' in key or 'Posterize' in key or 'Pixelate' in key or 'Grain' in key or 'Vignette' in key or 'Chromatic' in key or 'Glare' in key or 'Edge' in key:
            categories['Image/Effects'].append(key)
        elif 'Rotate' in key or 'Scale' in key or 'Crop' in key or 'Flip' in key or 'Transform' in key or 'Translate' in key:
            categories['Image/Transform'].append(key)
        elif 'Compress' in key or 'LoadText' in key or 'RandomLine' in key:
            categories['IO'].append(key)
        elif 'Ollama' in key or 'OpenAI' in key or 'Claude' in key or 'Gemini' in key:
            categories['LLMs'].append(key)
        elif 'Upload' in key or 'S3' in key:
            categories['Upload'].append(key)

    for category, nodes in categories.items():
        print(f"  {category}: {len(nodes)} nodes")
        if nodes:
            for node in sorted(nodes):
                print(f"    ✓ {node}")
        else:
            print(f"    ✗ No nodes loaded!")

    print("\n" + "=" * 80)

    if len(mappings) < 35:
        print(f"⚠ WARNING: Expected 35 nodes, but only {len(mappings)} loaded!")
        print("\nMissing image nodes? Check ComfyUI console for import errors.")
        print("Common issues:")
        print("  1. Missing dependencies (Pillow, numpy)")
        print("  2. Syntax errors in node files")
        print("  3. Import path issues")
    else:
        print("✓ All 35 nodes loaded successfully!")

    print("=" * 80)
else:
    print("✗ NODE_CLASS_MAPPINGS not found in module")

# Try importing nodes directly
print("\nTesting direct imports:")
print("-" * 80)

test_nodes = [
    ('nodes.image.effects.invert_node', 'IsekaiInvert'),
    ('nodes.image.effects.blur_node', 'IsekaiBlur'),
    ('nodes.image.blend.blend_node', 'IsekaiBlend'),
    ('nodes.image.transform.rotate_node', 'IsekaiRotate'),
]

for module_path, class_name in test_nodes:
    try:
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        print(f"✓ {class_name}: {cls.CATEGORY}")
    except Exception as e:
        print(f"✗ {class_name}: {type(e).__name__}: {e}")

print("=" * 80)
