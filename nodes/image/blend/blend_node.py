"""
Isekai Blend Node for ComfyUI

Blends two images using various blend modes.
"""

from typing import Tuple
import torch
from PIL import Image, ImageChops

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiBlend:
    """
    Blend two images together.

    Supports multiple blend modes:
    - Normal: Simple opacity blend
    - Multiply: Darkens image
    - Screen: Lightens image
    - Add: Adds color values
    - Subtract: Subtracts color values
    - Difference: Absolute difference
    - Lighten: Keep lighter pixels
    - Darken: Keep darker pixels

    Category: Isekai/Image/Blend
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_a": ("IMAGE",),
                "image_b": ("IMAGE",),
                "blend_mode": ([
                    "Normal",
                    "Multiply",
                    "Screen",
                    "Add",
                    "Subtract",
                    "Difference",
                    "Lighten",
                    "Darken"
                ],),
            },
            "optional": {
                "opacity": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Blend"

    def apply(
        self,
        image_a: torch.Tensor,
        image_b: torch.Tensor,
        blend_mode: str,
        opacity: float = 1.0
    ) -> Tuple[torch.Tensor]:
        """
        Blend two images.

        Args:
            image_a: Base image tensor
            image_b: Blend image tensor
            blend_mode: Blending mode
            opacity: Blend opacity (0=image_a only, 1=full blend)

        Returns:
            Tuple containing the blended image tensor
        """
        try:
            # Convert tensors to PIL
            pil_image_a = tensor_to_pil(image_a)
            pil_image_b = tensor_to_pil(image_b)

            # Ensure RGB mode
            if pil_image_a.mode != 'RGB':
                pil_image_a = pil_image_a.convert('RGB')
            if pil_image_b.mode != 'RGB':
                pil_image_b = pil_image_b.convert('RGB')

            # Resize image_b to match image_a if needed
            if pil_image_a.size != pil_image_b.size:
                pil_image_b = pil_image_b.resize(pil_image_a.size, Image.LANCZOS)

            # Apply blend mode
            if blend_mode == "Normal":
                blended = pil_image_b
            elif blend_mode == "Multiply":
                blended = ImageChops.multiply(pil_image_a, pil_image_b)
            elif blend_mode == "Screen":
                blended = ImageChops.screen(pil_image_a, pil_image_b)
            elif blend_mode == "Add":
                blended = ImageChops.add(pil_image_a, pil_image_b)
            elif blend_mode == "Subtract":
                blended = ImageChops.subtract(pil_image_a, pil_image_b)
            elif blend_mode == "Difference":
                blended = ImageChops.difference(pil_image_a, pil_image_b)
            elif blend_mode == "Lighten":
                blended = ImageChops.lighter(pil_image_a, pil_image_b)
            elif blend_mode == "Darken":
                blended = ImageChops.darker(pil_image_a, pil_image_b)
            else:
                blended = pil_image_b

            # Apply opacity
            if opacity < 1.0:
                result = Image.blend(pil_image_a, blended, opacity)
            else:
                result = blended

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Blend Error: {str(e)}")
            return (image_a,)  # Return base image on error
