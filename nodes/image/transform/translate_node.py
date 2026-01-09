"""
Isekai Translate Node for ComfyUI

Shifts/translates image position.
"""

from typing import Tuple
import torch
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiTranslate:
    """
    Translate/shift image.

    Moves the image by specified horizontal and vertical offsets.
    Empty areas are filled with black by default.

    Category: Isekai/Image/Transform
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "x_offset": ("INT", {
                    "default": 0,
                    "min": -8192,
                    "max": 8192,
                    "step": 1
                }),
                "y_offset": ("INT", {
                    "default": 0,
                    "min": -8192,
                    "max": 8192,
                    "step": 1
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Transform"

    def apply(
        self,
        image: torch.Tensor,
        x_offset: int,
        y_offset: int
    ) -> Tuple[torch.Tensor]:
        """
        Translate image.

        Args:
            image: Input image tensor
            x_offset: Horizontal offset (positive=right, negative=left)
            y_offset: Vertical offset (positive=down, negative=up)

        Returns:
            Tuple containing the translated image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Skip if no offset
            if x_offset == 0 and y_offset == 0:
                return (pil_to_tensor(pil_image),)

            # Create new image with same size, paste with offset
            width, height = pil_image.size
            result = Image.new('RGB', (width, height), (0, 0, 0))
            result.paste(pil_image, (x_offset, y_offset))

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Translate Error: {str(e)}")
            return (image,)  # Return original on error
