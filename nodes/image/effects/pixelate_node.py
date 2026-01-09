"""
Isekai Pixelate Node for ComfyUI

Creates a mosaic/pixelated effect by downsampling and upsampling.
"""

from typing import Tuple
import torch
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiPixelate:
    """
    Pixelate image (mosaic effect).

    Creates a pixel art or mosaic effect by downsampling the image
    and then upsampling it back to original size.

    Category: Isekai/Image/Effects
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "pixel_size": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "slider"
                }),
            },
            "optional": {
                "sampling": (["Nearest", "Bilinear"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Effects"

    def apply(
        self,
        image: torch.Tensor,
        pixel_size: int,
        sampling: str = "Nearest"
    ) -> Tuple[torch.Tensor]:
        """
        Apply pixelate effect.

        Args:
            image: Input image tensor
            pixel_size: Size of pixels (1-100, higher = more pixelated)
            sampling: Upsampling method (Nearest for sharp pixels, Bilinear for smooth)

        Returns:
            Tuple containing the pixelated image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Skip if pixel_size is 1
            if pixel_size == 1:
                return (pil_to_tensor(pil_image),)

            # Get original dimensions
            width, height = pil_image.size

            # Calculate downsampled size
            small_width = max(1, width // pixel_size)
            small_height = max(1, height // pixel_size)

            # Downsample (always use NEAREST for pixelation)
            small = pil_image.resize((small_width, small_height), Image.NEAREST)

            # Upsample back to original size
            if sampling == "Nearest":
                result = small.resize((width, height), Image.NEAREST)
            else:  # Bilinear
                result = small.resize((width, height), Image.BILINEAR)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Pixelate Error: {str(e)}")
            return (image,)  # Return original on error
