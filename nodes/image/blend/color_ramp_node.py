"""
Isekai Color Ramp Node for ComfyUI

Maps colors using a gradient/LUT.
"""

from typing import Tuple
import torch
import numpy as np
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiColorRamp:
    """
    Color ramp (gradient mapping).

    Maps image brightness to colors using a gradient.
    Useful for color grading and stylization.

    Category: Isekai/Image/Blend
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "preset": (["Cool to Warm", "Blue to Yellow", "Purple to Orange", "Grayscale"],),
            },
            "optional": {
                "intensity": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
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
        preset: str,
        intensity: float = 1.0
    ) -> Tuple[torch.Tensor]:
        """
        Apply color ramp.

        Args:
            image: Input image tensor
            preset: Color ramp preset
            intensity: Effect intensity

        Returns:
            Tuple containing the color-mapped image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Convert to numpy
            img_array = np.array(pil_image).astype(np.float32)

            # Calculate brightness
            brightness = np.mean(img_array, axis=2) / 255.0

            # Define color ramps (start_color, end_color)
            ramps = {
                "Cool to Warm": (np.array([0, 100, 200]), np.array([200, 100, 0])),
                "Blue to Yellow": (np.array([0, 50, 200]), np.array([255, 255, 0])),
                "Purple to Orange": (np.array([100, 0, 200]), np.array([255, 150, 0])),
                "Grayscale": (np.array([0, 0, 0]), np.array([255, 255, 255]))
            }

            start_color, end_color = ramps.get(preset, ramps["Cool to Warm"])

            # Apply gradient mapping
            result_array = np.zeros_like(img_array)
            for c in range(3):
                result_array[:, :, c] = start_color[c] + (end_color[c] - start_color[c]) * brightness

            # Blend with original
            if intensity < 1.0:
                result_array = img_array * (1 - intensity) + result_array * intensity

            result_array = np.clip(result_array, 0, 255).astype(np.uint8)
            result = Image.fromarray(result_array)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Color Ramp Error: {str(e)}")
            return (image,)  # Return original on error
