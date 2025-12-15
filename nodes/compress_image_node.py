"""
Isekai Compress Image Node for ComfyUI

This module provides functionality to compress images with configurable format
and quality settings before upload or save operations.
"""

from typing import Tuple, Dict, Any

import torch
from PIL import Image

# Try relative imports first (production), fall back to absolute
try:
    from ..utils.image_utils import tensor_to_pil, pil_to_bytes, pil_to_tensor
    from .base import IsekaiCompressionError
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_bytes, pil_to_tensor
    from nodes.base import IsekaiCompressionError


class IsekaiCompressImage:
    """
    ComfyUI custom node for compressing images with format and quality control.

    This node takes an image tensor, compresses it using the specified format
    (PNG, JPEG, or WEBP) and quality preset, then returns the compressed image
    as a tensor. The output maintains ComfyUI IMAGE tensor format and can be
    chained with upload or save nodes.

    Attributes:
        RETURN_TYPES: Tuple containing ("IMAGE",)
        RETURN_NAMES: Tuple containing ("compressed_image",)
        FUNCTION: "compress_image"
        CATEGORY: "Isekai"
        OUTPUT_NODE: False (can be chained with other nodes)

    Example:
        This node is typically connected in a workflow like:
        Load Image -> Compress Image -> Upload/Save Image

    Supported Formats:
        - PNG: Lossless compression, best for workflows, largest files
        - JPEG: Lossy compression, no transparency, good for photos
        - WEBP: Modern format with excellent compression, lossy or lossless

    Presets:
        - Maximum Quality: Minimal compression, best quality, largest files
        - High Quality: Good compression with excellent quality (recommended)
        - Balanced: Balance between quality and file size
        - Maximum Compression: Smallest files, some quality loss acceptable
        - Custom: Manual quality control via slider
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required and optional input specifications:
            - image: ComfyUI IMAGE tensor
            - format: Image format selection (PNG, JPEG, WEBP)
            - preset: Quality preset selection
            - quality: Manual quality control (only used when preset is Custom)
        """
        return {
            "required": {
                "image": ("IMAGE",),
                "format": (["PNG", "JPEG", "WEBP"],),
                "preset": ([
                    "Maximum Quality",
                    "High Quality",
                    "Balanced",
                    "Maximum Compression",
                    "Custom"
                ],),
            },
            "optional": {
                "quality": ("INT", {
                    "default": 85,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "slider"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("compressed_image",)
    FUNCTION = "compress_image"
    CATEGORY = "Isekai"
    OUTPUT_NODE = False

    def _get_save_kwargs(self, format: str, preset: str, custom_quality: int) -> dict:
        """
        Map preset and format to PIL Image.save() kwargs.

        Args:
            format: Image format ('PNG', 'JPEG', 'WEBP')
            preset: Quality preset name
            custom_quality: Quality value when preset='Custom'

        Returns:
            Dictionary of kwargs to pass to Image.save()

        Preset Mappings:
            Maximum Quality:
                - PNG: compress_level=6, optimize=False
                - JPEG: quality=95, optimize=False
                - WEBP: lossless=True

            High Quality (Recommended):
                - PNG: compress_level=6, optimize=True
                - JPEG: quality=85, optimize=True
                - WEBP: quality=90, lossless=False

            Balanced:
                - PNG: compress_level=9, optimize=True
                - JPEG: quality=75, optimize=True
                - WEBP: quality=80, lossless=False

            Maximum Compression:
                - PNG: compress_level=9, optimize=True
                - JPEG: quality=60, optimize=True
                - WEBP: quality=60, lossless=False

            Custom:
                - PNG: compress_level=9, optimize=True
                - JPEG: quality=custom_quality, optimize=True
                - WEBP: quality=custom_quality, lossless=False
        """
        presets = {
            "Maximum Quality": {
                "PNG": {"compress_level": 6, "optimize": False},
                "JPEG": {"quality": 95, "optimize": False},
                "WEBP": {"lossless": True},
            },
            "High Quality": {
                "PNG": {"compress_level": 6, "optimize": True},
                "JPEG": {"quality": 85, "optimize": True},
                "WEBP": {"quality": 90, "lossless": False},
            },
            "Balanced": {
                "PNG": {"compress_level": 9, "optimize": True},
                "JPEG": {"quality": 75, "optimize": True},
                "WEBP": {"quality": 80, "lossless": False},
            },
            "Maximum Compression": {
                "PNG": {"compress_level": 9, "optimize": True},
                "JPEG": {"quality": 60, "optimize": True},
                "WEBP": {"quality": 60, "lossless": False},
            },
            "Custom": {
                "PNG": {"compress_level": 9, "optimize": True},
                "JPEG": {"quality": custom_quality, "optimize": True},
                "WEBP": {"quality": custom_quality, "lossless": False},
            }
        }

        return presets[preset][format]

    def compress_image(
        self,
        image: torch.Tensor,
        format: str,
        preset: str,
        quality: int = 85
    ) -> Tuple[torch.Tensor]:
        """
        Compress image using specified format and preset.

        This method performs a round-trip conversion:
        tensor -> PIL -> compressed bytes -> PIL -> tensor

        The compression is done in-memory using BytesIO buffers for efficiency.
        If compression fails for any reason, the original image is returned
        unchanged with an error message printed to console.

        Args:
            image: ComfyUI IMAGE tensor [B,H,W,C], float32, range [0.0,1.0]
            format: Image format ('PNG', 'JPEG', 'WEBP')
            preset: Quality preset (Maximum Quality, High Quality, Balanced,
                                   Maximum Compression, Custom)
            quality: Custom quality value (1-100, only used when preset='Custom')

        Returns:
            Tuple containing compressed image as tensor [1,H,W,C], float32, [0.0,1.0]
            If compression fails, returns original image unchanged

        Example:
            >>> node = IsekaiCompressImage()
            >>> image_tensor = torch.rand(1, 512, 512, 3)
            >>> compressed = node.compress_image(image_tensor, "JPEG", "High Quality")
            >>> compressed[0].shape
            torch.Size([1, 512, 512, 3])
        """
        try:
            # Get format-specific save parameters
            save_kwargs = self._get_save_kwargs(format, preset, quality)

            # Log compression start
            print(f"[Isekai] Compressing image with format={format}, preset={preset}")
            if preset == "Custom":
                print(f"[Isekai] Using custom quality={quality}")

            # Step 1: Convert tensor to PIL Image (handles batch, takes first image)
            pil_image = tensor_to_pil(image)

            # Log original image info
            print(f"[Isekai] Original image size: {pil_image.width}x{pil_image.height}, mode: {pil_image.mode}")

            # Step 2: Compress to bytes buffer
            compressed_buffer = pil_to_bytes(pil_image, format=format, **save_kwargs)

            # Step 3: Get compressed size
            compressed_size = compressed_buffer.seek(0, 2)  # Seek to end to get size
            compressed_buffer.seek(0)  # Reset to beginning

            # Step 4: Reload from compressed bytes
            compressed_pil = Image.open(compressed_buffer)

            # Step 5: Ensure RGB mode (JPEG may change mode, transparency handling)
            if compressed_pil.mode != 'RGB':
                print(f"[Isekai] Converting from {compressed_pil.mode} to RGB mode")
                compressed_pil = compressed_pil.convert('RGB')

            # Step 6: Convert back to tensor
            output_tensor = pil_to_tensor(compressed_pil)

            # Log compression results
            print(f"[Isekai] Compression successful!")
            print(f"[Isekai] Compressed size: {compressed_size / 1024:.2f} KB")
            print(f"[Isekai] Output tensor shape: {output_tensor.shape}, dtype: {output_tensor.dtype}")

            # Close PIL images to free memory
            compressed_pil.close()
            compressed_buffer.close()

            return (output_tensor,)

        except Exception as e:
            # Log error and return original image as fallback
            print(f"[Isekai] Compression failed: {str(e)}")
            print(f"[Isekai] Error type: {type(e).__name__}")
            print(f"[Isekai] Returning original image unchanged")
            return (image,)
