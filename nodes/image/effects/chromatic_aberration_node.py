"""
Isekai Chromatic Aberration Node for ComfyUI

Creates RGB channel offset effect (lens aberration).
"""

from typing import Tuple
import torch
import numpy as np
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiChromaticAberration:
    """
    Chromatic aberration effect.

    Simulates lens chromatic aberration by offsetting RGB channels.
    Creates colorful fringing effect around edges.

    Category: Isekai/Image/Effects
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "strength": ("FLOAT", {
                    "default": 5.0,
                    "min": 0.0,
                    "max": 50.0,
                    "step": 0.1,
                    "display": "slider"
                }),
            },
            "optional": {
                "angle": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 360.0,
                    "step": 1.0
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
        strength: float,
        angle: float = 0.0
    ) -> Tuple[torch.Tensor]:
        """
        Apply chromatic aberration.

        Args:
            image: Input image tensor
            strength: Aberration strength (pixel offset)
            angle: Aberration direction in degrees

        Returns:
            Tuple containing the aberrated image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Skip if strength is 0
            if strength == 0:
                return (pil_to_tensor(pil_image),)

            # Convert to numpy
            img_array = np.array(pil_image)

            # Calculate offsets based on angle
            angle_rad = np.radians(angle)
            offset_x = int(strength * np.cos(angle_rad))
            offset_y = int(strength * np.sin(angle_rad))

            # Create output array
            result_array = img_array.copy()

            # Offset red channel
            if offset_x != 0 or offset_y != 0:
                result_array[:, :, 0] = np.roll(img_array[:, :, 0], (offset_y, offset_x), axis=(0, 1))

            # Offset blue channel (opposite direction)
            if offset_x != 0 or offset_y != 0:
                result_array[:, :, 2] = np.roll(img_array[:, :, 2], (-offset_y, -offset_x), axis=(0, 1))

            # Green channel stays in place
            result = Image.fromarray(result_array)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Chromatic Aberration Error: {str(e)}")
            return (image,)  # Return original on error
