"""
Isekai Vignette Node for ComfyUI

Adds a vignette effect (darkened edges).
"""

from typing import Tuple
import torch
import numpy as np
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiVignette:
    """
    Add vignette effect.

    Darkens the edges of the image, creating a focus effect towards the center.
    Commonly used in photography and cinematography.

    Category: Isekai/Image/Effects
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "intensity": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
            },
            "optional": {
                "radius": ("FLOAT", {
                    "default": 0.8,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "softness": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.01,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
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
        intensity: float,
        radius: float = 0.8,
        softness: float = 0.5
    ) -> Tuple[torch.Tensor]:
        """
        Apply vignette effect.

        Args:
            image: Input image tensor
            intensity: Vignette intensity (0-1)
            radius: Vignette radius (0=center, 1=edge)
            softness: Edge softness (higher=softer transition)

        Returns:
            Tuple containing the vignetted image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Skip if intensity is 0
            if intensity == 0:
                return (pil_to_tensor(pil_image),)

            # Get dimensions
            width, height = pil_image.size
            center_x, center_y = width / 2, height / 2

            # Create coordinate grid
            y, x = np.ogrid[:height, :width]
            dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)

            # Normalize distance
            max_dist = np.sqrt(center_x**2 + center_y**2)
            dist_normalized = dist_from_center / max_dist

            # Apply vignette curve
            mask = np.clip((dist_normalized - radius) / softness, 0, 1)
            mask = 1 - (mask * intensity)

            # Apply mask to image
            img_array = np.array(pil_image).astype(np.float32)
            result_array = img_array * mask[:, :, np.newaxis]
            result_array = np.clip(result_array, 0, 255).astype(np.uint8)
            result = Image.fromarray(result_array)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Vignette Error: {str(e)}")
            return (image,)  # Return original on error
