"""
Isekai Posterize Node for ComfyUI

Reduces the number of colors in an image by reducing bits per channel.
"""

from typing import Tuple
import torch
from PIL import ImageOps

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiPosterize:
    """
    Posterize image (reduce color levels).

    Reduces the number of bits for each color channel, creating a
    poster-like effect with fewer distinct colors.

    Category: Isekai/Image/Effects
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "bits": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 8,
                    "step": 1,
                    "display": "slider"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Effects"

    def apply(self, image: torch.Tensor, bits: int) -> Tuple[torch.Tensor]:
        """
        Posterize image by reducing bits per channel.

        Args:
            image: Input image tensor
            bits: Number of bits per channel (1-8, lower = fewer colors)

        Returns:
            Tuple containing the posterized image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Posterize
            result = ImageOps.posterize(pil_image, bits)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Posterize Error: {str(e)}")
            return (image,)  # Return original on error
