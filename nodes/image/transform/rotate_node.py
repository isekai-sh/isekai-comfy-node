"""
Isekai Rotate Node for ComfyUI

Rotates images by a specified angle.
"""

from typing import Tuple
import torch
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiRotate:
    """
    Rotate image by angle.

    Rotates the image by the specified angle in degrees.
    Supports expanding the canvas to fit the rotated image.

    Category: Isekai/Image/Transform
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "angle": ("FLOAT", {
                    "default": 0.0,
                    "min": -360.0,
                    "max": 360.0,
                    "step": 0.1,
                    "display": "slider"
                }),
            },
            "optional": {
                "expand": ("BOOLEAN", {
                    "default": False
                }),
                "resample": (["Nearest", "Bilinear", "Bicubic"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Transform"

    def apply(
        self,
        image: torch.Tensor,
        angle: float,
        expand: bool = False,
        resample: str = "Bilinear"
    ) -> Tuple[torch.Tensor]:
        """
        Rotate image.

        Args:
            image: Input image tensor
            angle: Rotation angle in degrees (counter-clockwise)
            expand: If True, expand canvas to fit rotated image
            resample: Resampling method for quality

        Returns:
            Tuple containing the rotated image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Skip if angle is 0
            if angle == 0:
                return (pil_to_tensor(pil_image),)

            # Map resample method
            resample_map = {
                "Nearest": Image.NEAREST,
                "Bilinear": Image.BILINEAR,
                "Bicubic": Image.BICUBIC
            }

            # Rotate image
            result = pil_image.rotate(
                angle,
                resample=resample_map.get(resample, Image.BILINEAR),
                expand=expand
            )

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Rotate Error: {str(e)}")
            return (image,)  # Return original on error
