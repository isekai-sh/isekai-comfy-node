"""
Isekai Glare Node for ComfyUI

Creates a bloom/glare light effect.
"""

from typing import Tuple
import torch
import numpy as np
from PIL import Image, ImageFilter

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiGlare:
    """
    Add glare/bloom effect.

    Creates a glowing effect by blurring bright areas and adding them back.
    Simulates lens bloom and light scatter.

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
                "threshold": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "blur_radius": ("FLOAT", {
                    "default": 15.0,
                    "min": 1.0,
                    "max": 50.0,
                    "step": 0.5
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
        threshold: float = 0.7,
        blur_radius: float = 15.0
    ) -> Tuple[torch.Tensor]:
        """
        Apply glare/bloom effect.

        Args:
            image: Input image tensor
            intensity: Glare intensity
            threshold: Brightness threshold for glare (0-1)
            blur_radius: Blur size for glow

        Returns:
            Tuple containing the glared image tensor
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

            # Convert to numpy
            img_array = np.array(pil_image).astype(np.float32) / 255.0

            # Extract bright areas
            brightness = np.mean(img_array, axis=2)
            bright_mask = brightness > threshold
            bright_mask = bright_mask[:, :, np.newaxis]

            # Create bright-only image
            bright_img_array = img_array * bright_mask
            bright_img = Image.fromarray((bright_img_array * 255).astype(np.uint8))

            # Blur the bright areas
            blurred = bright_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            blurred_array = np.array(blurred).astype(np.float32) / 255.0

            # Add blurred glow to original
            result_array = img_array + (blurred_array * intensity)
            result_array = np.clip(result_array * 255, 0, 255).astype(np.uint8)
            result = Image.fromarray(result_array)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Glare Error: {str(e)}")
            return (image,)  # Return original on error
