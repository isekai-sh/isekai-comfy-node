"""
Isekai Color Adjust Node for ComfyUI

Adjusts brightness, contrast, saturation, and sharpness.
"""

from typing import Tuple
import torch
from PIL import ImageEnhance

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiColorAdjust:
    """
    Adjust image color properties.

    Provides controls for:
    - Brightness: Lighten or darken
    - Contrast: Increase or decrease contrast
    - Saturation: More or less colorful
    - Sharpness: Sharpen or soften details

    Category: Isekai/Image/Blend
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "brightness": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "contrast": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "saturation": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "sharpness": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
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
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0
    ) -> Tuple[torch.Tensor]:
        """
        Adjust image properties.

        Args:
            image: Input image tensor
            brightness: Brightness factor (0=black, 1=original, 2=very bright)
            contrast: Contrast factor (0=gray, 1=original, 2=high contrast)
            saturation: Color saturation (0=grayscale, 1=original, 2=very saturated)
            sharpness: Sharpness factor (0=blurry, 1=original, 2=very sharp)

        Returns:
            Tuple containing the adjusted image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            result = pil_image

            # Apply adjustments in sequence
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(result)
                result = enhancer.enhance(brightness)

            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(result)
                result = enhancer.enhance(contrast)

            if saturation != 1.0:
                enhancer = ImageEnhance.Color(result)
                result = enhancer.enhance(saturation)

            if sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(result)
                result = enhancer.enhance(sharpness)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Color Adjust Error: {str(e)}")
            return (image,)  # Return original on error
