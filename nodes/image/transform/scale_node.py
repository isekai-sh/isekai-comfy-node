"""
Isekai Scale Node for ComfyUI

Resizes images using various methods and quality options.
"""

from typing import Tuple
import torch
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiScale:
    """
    Scale/Resize images.

    Supports multiple scaling methods:
    - Factor: Scale by multiplication factor
    - Dimensions: Scale to exact width/height
    - Percentage: Scale by percentage

    Category: Isekai/Image/Transform
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "scale_method": (["Factor", "Dimensions", "Percentage"],),
            },
            "optional": {
                "scale_x": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.01,
                    "max": 10.0,
                    "step": 0.01
                }),
                "scale_y": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.01,
                    "max": 10.0,
                    "step": 0.01
                }),
                "width": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 8192,
                    "step": 1
                }),
                "height": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 8192,
                    "step": 1
                }),
                "resampling": (["Nearest", "Bilinear", "Bicubic", "Lanczos"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Transform"

    def apply(
        self,
        image: torch.Tensor,
        scale_method: str,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        width: int = 512,
        height: int = 512,
        resampling: str = "Lanczos"
    ) -> Tuple[torch.Tensor]:
        """
        Scale image.

        Args:
            image: Input image tensor
            scale_method: Scaling method (Factor, Dimensions, or Percentage)
            scale_x: X scale factor or percentage
            scale_y: Y scale factor or percentage
            width: Target width (for Dimensions method)
            height: Target height (for Dimensions method)
            resampling: Resampling quality

        Returns:
            Tuple containing the scaled image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Get original dimensions
            orig_width, orig_height = pil_image.size

            # Calculate new dimensions based on method
            if scale_method == "Factor":
                new_width = int(orig_width * scale_x)
                new_height = int(orig_height * scale_y)
            elif scale_method == "Percentage":
                new_width = int(orig_width * (scale_x / 100.0))
                new_height = int(orig_height * (scale_y / 100.0))
            else:  # Dimensions
                new_width = width
                new_height = height

            # Ensure dimensions are at least 1
            new_width = max(1, new_width)
            new_height = max(1, new_height)

            # Skip if dimensions haven't changed
            if new_width == orig_width and new_height == orig_height:
                return (pil_to_tensor(pil_image),)

            # Map resampling method
            resample_map = {
                "Nearest": Image.NEAREST,
                "Bilinear": Image.BILINEAR,
                "Bicubic": Image.BICUBIC,
                "Lanczos": Image.LANCZOS
            }

            # Resize image
            result = pil_image.resize(
                (new_width, new_height),
                resample=resample_map.get(resampling, Image.LANCZOS)
            )

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Scale Error: {str(e)}")
            return (image,)  # Return original on error
