"""
Isekai Compress and Save Node for ComfyUI

This module provides functionality to compress and save images with configurable
format and quality settings.
"""

import os
from pathlib import Path
from typing import Tuple, Dict, Any

import torch
from PIL import Image

# Try relative imports first (production), fall back to absolute
try:
    from ..utils.image_utils import tensor_to_pil
    from .base import IsekaiCompressionError
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil
    from nodes.base import IsekaiCompressionError


class IsekaiCompressAndSave:
    """
    ComfyUI custom node for compressing and saving images to disk.

    This node takes an image tensor, compresses it with the specified format
    and quality, then saves it to the ComfyUI/output folder. Files are saved
    with customizable filename, prefix, and suffix.

    Attributes:
        RETURN_TYPES: Tuple (empty - node doesn't return values)
        FUNCTION: "save_image"
        CATEGORY: "Isekai"
        OUTPUT_NODE: True (terminal node, displays in UI)

    Supported Formats:
        - PNG: Lossless compression
        - JPEG: Lossy compression, smaller files
        - WEBP: Modern format with excellent compression
    """

    def __init__(self):
        self.output_dir = self._get_output_directory()
        self.type = "output"

    def _get_output_directory(self) -> Path:
        """
        Get ComfyUI output directory, creating if needed.

        Returns:
            Path to output directory
        """
        # Try to find ComfyUI output directory
        output_dir = Path("output")

        # Check if we're in custom_nodes subdirectory
        if not output_dir.exists():
            # Go up directories to find ComfyUI root
            current = Path.cwd()
            for _ in range(4):  # Search up to 4 levels
                potential_output = current / "output"
                if potential_output.exists():
                    output_dir = potential_output
                    break
                current = current.parent

        # Create if doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required and optional input specifications
        """
        return {
            "required": {
                "images": ("IMAGE",),
                "filename": ("STRING", {
                    "default": "isekai",
                    "multiline": False
                }),
                "format": (["JPEG", "PNG", "WEBP"], {
                    "default": "JPEG"
                }),
                "quality": ("INT", {
                    "default": 90,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "slider"
                }),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    CATEGORY = "Isekai"
    OUTPUT_NODE = True

    def _get_save_kwargs(self, format: str, quality: int) -> dict:
        """
        Get PIL Image.save() kwargs based on format and quality.

        Args:
            format: Image format ('PNG', 'JPEG', 'WEBP')
            quality: Quality value (1-100)

        Returns:
            Dictionary of kwargs to pass to Image.save()
        """
        if format == "PNG":
            # PNG: map quality to compress_level (0-9)
            compress_level = max(0, min(9, int((100 - quality) / 11)))
            return {"compress_level": compress_level, "optimize": True}
        elif format == "JPEG":
            return {"quality": quality, "optimize": True}
        else:  # WEBP
            return {"quality": quality, "lossless": (quality >= 95)}

    def _generate_filename(
        self,
        base_filename: str,
        format: str,
        counter: int
    ) -> str:
        """
        Generate filename with counter and extension.

        Args:
            base_filename: Base name for the file
            format: Image format (determines extension)
            counter: Counter number for the file

        Returns:
            Complete filename with extension
        """
        extension = {
            "PNG": "png",
            "JPEG": "jpg",
            "WEBP": "webp"
        }[format]

        return f"{base_filename}_{counter:05d}.{extension}"

    def save_images(
        self,
        images: torch.Tensor,
        filename: str = "isekai",
        format: str = "JPEG",
        quality: int = 90,
        prompt=None,
        extra_pnginfo=None
    ) -> Dict[str, Any]:
        """
        Save compressed images to disk.

        Args:
            images: Batch of images as tensor [B,H,W,C]
            filename: Base filename
            format: Image format (JPEG, PNG, WEBP)
            quality: Compression quality (1-100)
            prompt: ComfyUI prompt metadata (hidden)
            extra_pnginfo: Extra PNG metadata (hidden)

        Returns:
            Dictionary with UI information
        """
        results = []
        counter = 1

        # Get save parameters
        save_kwargs = self._get_save_kwargs(format, quality)

        print(f"[Isekai] Compressing and saving {len(images)} image(s)...")
        print(f"[Isekai] Format: {format}, Quality: {quality}")
        print(f"[Isekai] Save settings: {save_kwargs}")

        for (batch_number, image_tensor) in enumerate(images):
            # Add batch dimension if needed [H,W,C] → [1,H,W,C]
            if len(image_tensor.shape) == 3:
                image_tensor = image_tensor.unsqueeze(0)

            # Convert tensor to PIL
            pil_image = tensor_to_pil(image_tensor)

            # Find next available filename
            while True:
                full_filename = self._generate_filename(
                    filename, format, counter
                )
                file_path = self.output_dir / full_filename

                if not file_path.exists():
                    break
                counter += 1

            # Save with compression
            try:
                pil_image.save(str(file_path), format=format, **save_kwargs)

                # Get file size
                file_size_kb = file_path.stat().st_size / 1024

                print(f"[Isekai] Saved: {full_filename} ({file_size_kb:.2f} KB)")

                results.append({
                    "filename": full_filename,
                    "subfolder": "",
                    "type": self.type
                })

                counter += 1

            except Exception as e:
                print(f"[Isekai] Error saving {full_filename}: {str(e)}")
                raise IsekaiCompressionError(f"Failed to save image: {str(e)}")

        return {"ui": {"images": results}}
