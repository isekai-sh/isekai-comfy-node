"""
Isekai Grain Node for ComfyUI

Adds film grain/noise to images.
"""

from typing import Tuple
import torch
import numpy as np
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiGrain:
    """
    Add film grain/noise to images.

    Adds realistic film grain effect using various noise types.
    Supports monochrome or color noise.

    Category: Isekai/Image/Effects
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "intensity": ("FLOAT", {
                    "default": 0.1,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
            },
            "optional": {
                "grain_type": (["Gaussian", "Uniform"],),
                "monochrome": ("BOOLEAN", {
                    "default": True
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
        grain_type: str = "Gaussian",
        monochrome: bool = True
    ) -> Tuple[torch.Tensor]:
        """
        Add grain to image.

        Args:
            image: Input image tensor
            intensity: Grain intensity (0-1)
            grain_type: Type of noise (Gaussian or Uniform)
            monochrome: If True, same grain for all channels

        Returns:
            Tuple containing the grainy image tensor
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

            # Convert to numpy array
            img_array = np.array(pil_image).astype(np.float32)

            # Generate noise
            if monochrome:
                # Same noise for all channels
                if grain_type == "Gaussian":
                    noise = np.random.normal(0, intensity * 255, img_array.shape[:2])
                else:  # Uniform
                    noise = np.random.uniform(-intensity * 255, intensity * 255, img_array.shape[:2])
                noise = noise[:, :, np.newaxis]  # Add channel dimension
            else:
                # Separate noise per channel
                if grain_type == "Gaussian":
                    noise = np.random.normal(0, intensity * 255, img_array.shape)
                else:  # Uniform
                    noise = np.random.uniform(-intensity * 255, intensity * 255, img_array.shape)

            # Add noise and clip
            result_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
            result = Image.fromarray(result_array)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Grain Error: {str(e)}")
            return (image,)  # Return original on error
