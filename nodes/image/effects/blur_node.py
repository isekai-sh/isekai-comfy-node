"""
Isekai Blur Node for ComfyUI

Applies blur effects to images using various algorithms.
"""

from typing import Tuple
import torch
from PIL import ImageFilter

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiBlur:
    """
    Apply blur effects to images.

    Supports Gaussian and Box blur algorithms with adjustable radius.
    Gaussian blur creates smooth, natural-looking blur.
    Box blur is faster but less smooth.

    Category: Isekai/Image/Effects
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "blur_type": (["Gaussian", "Box"],),
                "radius": ("FLOAT", {
                    "default": 5.0,
                    "min": 0.0,
                    "max": 100.0,
                    "step": 0.1,
                    "display": "slider"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Effects"

    def apply(self, image: torch.Tensor, blur_type: str, radius: float) -> Tuple[torch.Tensor]:
        """
        Apply blur effect to image.

        Args:
            image: Input image tensor
            blur_type: Type of blur ("Gaussian" or "Box")
            radius: Blur radius (0-100)

        Returns:
            Tuple containing the blurred image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Skip if radius is 0
            if radius == 0:
                return (pil_to_tensor(pil_image),)

            # Apply blur based on type
            if blur_type == "Gaussian":
                result = pil_image.filter(ImageFilter.GaussianBlur(radius=radius))
            else:  # Box
                result = pil_image.filter(ImageFilter.BoxBlur(radius=radius))

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Blur Error: {str(e)}")
            return (image,)  # Return original on error
