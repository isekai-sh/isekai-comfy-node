"""
Isekai Crop Node for ComfyUI

Crops images to a specified region.
"""

from typing import Tuple
import torch

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiCrop:
    """
    Crop image to region.

    Crops the image to a rectangular region defined by position and size.
    Can crop from corner (x,y) or from center point.

    Category: Isekai/Image/Transform
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "x": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 1
                }),
                "y": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 1
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
            },
            "optional": {
                "from_center": ("BOOLEAN", {
                    "default": False
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
        x: int,
        y: int,
        width: int,
        height: int,
        from_center: bool = False
    ) -> Tuple[torch.Tensor]:
        """
        Crop image.

        Args:
            image: Input image tensor
            x: X position (left edge or center)
            y: Y position (top edge or center)
            width: Crop width
            height: Crop height
            from_center: If True, (x,y) is center point

        Returns:
            Tuple containing the cropped image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Calculate crop box
            if from_center:
                left = x - width // 2
                top = y - height // 2
            else:
                left = x
                top = y

            right = left + width
            bottom = top + height

            # Clamp to image bounds
            img_width, img_height = pil_image.size
            left = max(0, min(left, img_width))
            top = max(0, min(top, img_height))
            right = max(0, min(right, img_width))
            bottom = max(0, min(bottom, img_height))

            # Ensure valid crop region
            if right <= left or bottom <= top:
                print("[Isekai] Crop: Invalid crop region, returning original")
                return (image,)

            # Crop image
            result = pil_image.crop((left, top, right, bottom))

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Crop Error: {str(e)}")
            return (image,)  # Return original on error
