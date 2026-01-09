"""
Isekai Invert Node for ComfyUI

Inverts the colors of an image (creates a negative).
"""

from typing import Tuple
import torch
from PIL import ImageOps

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiInvert:
    """
    Invert image colors (create negative).

    Inverts all color values in the image, creating a negative effect.
    Black becomes white, white becomes black, colors are inverted.

    Category: Isekai/Image/Effects
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Effects"

    def apply(self, image: torch.Tensor) -> Tuple[torch.Tensor]:
        """
        Invert image colors.

        Args:
            image: Input image tensor

        Returns:
            Tuple containing the inverted image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Invert colors
            result = ImageOps.invert(pil_image)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Invert Error: {str(e)}")
            return (image,)  # Return original on error
