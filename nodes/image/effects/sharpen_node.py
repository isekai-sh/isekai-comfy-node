"""
Isekai Sharpen Node for ComfyUI

Sharpens images using various methods.
"""

from typing import Tuple
import torch
from PIL import ImageFilter

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiSharpen:
    """
    Sharpen images.

    Offers two sharpening methods:
    - Sharpen: Simple built-in sharpening filter
    - Unsharp Mask: Advanced sharpening with fine-tuned control

    Category: Isekai/Image/Effects
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "method": (["Sharpen", "Unsharp Mask"],),
            },
            "optional": {
                "radius": ("FLOAT", {
                    "default": 2.0,
                    "min": 0.0,
                    "max": 10.0,
                    "step": 0.1,
                    "display": "slider"
                }),
                "percent": ("INT", {
                    "default": 150,
                    "min": 0,
                    "max": 500,
                    "step": 1,
                    "display": "slider"
                }),
                "threshold": ("INT", {
                    "default": 3,
                    "min": 0,
                    "max": 255,
                    "step": 1,
                    "display": "slider"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Effects"

    def apply(
        self,
        image: torch.Tensor,
        method: str,
        radius: float = 2.0,
        percent: int = 150,
        threshold: int = 3
    ) -> Tuple[torch.Tensor]:
        """
        Sharpen image.

        Args:
            image: Input image tensor
            method: Sharpening method
            radius: Unsharp mask radius (for Unsharp Mask only)
            percent: Sharpening strength (for Unsharp Mask only)
            threshold: Edge threshold (for Unsharp Mask only)

        Returns:
            Tuple containing the sharpened image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Apply sharpening
            if method == "Sharpen":
                result = pil_image.filter(ImageFilter.SHARPEN)
            else:  # Unsharp Mask
                result = pil_image.filter(ImageFilter.UnsharpMask(
                    radius=radius,
                    percent=percent,
                    threshold=threshold
                ))

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Sharpen Error: {str(e)}")
            return (image,)  # Return original on error
