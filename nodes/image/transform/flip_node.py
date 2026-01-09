"""
Isekai Flip Node for ComfyUI

Flips images horizontally, vertically, or both.
"""

from typing import Tuple
import torch
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiFlip:
    """
    Flip image.

    Flips the image horizontally (mirror), vertically, or both.

    Category: Isekai/Image/Transform
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "direction": (["Horizontal", "Vertical", "Both"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Transform"

    def apply(self, image: torch.Tensor, direction: str) -> Tuple[torch.Tensor]:
        """
        Flip image.

        Args:
            image: Input image tensor
            direction: Flip direction (Horizontal, Vertical, or Both)

        Returns:
            Tuple containing the flipped image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Apply flip
            if direction == "Horizontal":
                result = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
            elif direction == "Vertical":
                result = pil_image.transpose(Image.FLIP_TOP_BOTTOM)
            else:  # Both
                result = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
                result = result.transpose(Image.FLIP_TOP_BOTTOM)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Flip Error: {str(e)}")
            return (image,)  # Return original on error
