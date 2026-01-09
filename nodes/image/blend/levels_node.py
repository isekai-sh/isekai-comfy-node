"""
Isekai Levels Node for ComfyUI

Adjusts black/white points and midtones.
"""

from typing import Tuple
import torch
import numpy as np
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiLevels:
    """
    Adjust image levels.

    Controls black point, white point, and midtone gamma.
    Similar to Levels adjustment in photo editors.

    Category: Isekai/Image/Blend
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "black_point": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 0.99,
                    "step": 0.01,
                    "display": "slider"
                }),
                "white_point": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.01,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "gamma": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.1,
                    "max": 3.0,
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
        image: torch.Tensor,
        black_point: float = 0.0,
        white_point: float = 1.0,
        gamma: float = 1.0
    ) -> Tuple[torch.Tensor]:
        """
        Adjust levels.

        Args:
            image: Input image tensor
            black_point: Input black point (0-1)
            white_point: Input white point (0-1)
            gamma: Midtone gamma correction

        Returns:
            Tuple containing the level-adjusted image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Convert to numpy (0-1 range)
            img_array = np.array(pil_image).astype(np.float32) / 255.0

            # Apply black and white points
            img_array = (img_array - black_point) / (white_point - black_point)
            img_array = np.clip(img_array, 0, 1)

            # Apply gamma correction
            if gamma != 1.0:
                img_array = np.power(img_array, 1.0 / gamma)

            # Convert back to 0-255
            result_array = (img_array * 255).astype(np.uint8)
            result = Image.fromarray(result_array)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Levels Error: {str(e)}")
            return (image,)  # Return original on error
