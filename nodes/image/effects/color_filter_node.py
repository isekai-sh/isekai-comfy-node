"""
Isekai Color Filter Node for ComfyUI

Applies color filters like sepia, grayscale, and black & white.
"""

from typing import Tuple
import torch
import numpy as np
from PIL import Image, ImageOps

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiColorFilter:
    """
    Apply color filters to images.

    Supports various color filter effects:
    - Sepia: Warm, vintage tone
    - Grayscale: Remove all color
    - Black & White: High contrast monochrome
    - None: Pass through (useful for intensity blending)

    Category: Isekai/Image/Effects
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "filter_type": (["None", "Sepia", "Grayscale", "Black & White"],),
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
    CATEGORY = "Isekai/Image/Effects"

    def apply(
        self,
        image: torch.Tensor,
        filter_type: str,
        intensity: float = 1.0
    ) -> Tuple[torch.Tensor]:
        """
        Apply color filter.

        Args:
            image: Input image tensor
            filter_type: Type of filter to apply
            intensity: Filter intensity (0=original, 1=full effect)

        Returns:
            Tuple containing the filtered image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Return original if no filter
            if filter_type == "None" or intensity == 0:
                return (pil_to_tensor(pil_image),)

            # Apply filter based on type
            if filter_type == "Grayscale":
                filtered = ImageOps.grayscale(pil_image).convert('RGB')
            elif filter_type == "Black & White":
                # High contrast black & white
                gray = pil_image.convert('L')
                bw = gray.point(lambda x: 0 if x < 128 else 255)
                filtered = bw.convert('RGB')
            elif filter_type == "Sepia":
                # Apply sepia tone using color matrix
                img_array = np.array(pil_image).astype(np.float32)

                # Sepia transformation matrix
                sepia_matrix = np.array([
                    [0.393, 0.769, 0.189],
                    [0.349, 0.686, 0.168],
                    [0.272, 0.534, 0.131]
                ])

                # Apply matrix transformation
                sepia_array = img_array @ sepia_matrix.T
                sepia_array = np.clip(sepia_array, 0, 255).astype(np.uint8)
                filtered = Image.fromarray(sepia_array)
            else:
                filtered = pil_image

            # Blend with original based on intensity
            if intensity < 1.0:
                result = Image.blend(pil_image, filtered, intensity)
            else:
                result = filtered

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Color Filter Error: {str(e)}")
            return (image,)  # Return original on error
