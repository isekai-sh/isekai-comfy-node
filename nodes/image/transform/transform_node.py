"""
Isekai Transform Node for ComfyUI

Combined transformation node (rotate, scale, translate).
"""

from typing import Tuple
import torch
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiTransform:
    """
    Combined transform operations.

    Applies rotation, scaling, and translation in a single operation.
    More efficient than chaining multiple transform nodes.

    Category: Isekai/Image/Transform
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "angle": ("FLOAT", {
                    "default": 0.0,
                    "min": -360.0,
                    "max": 360.0,
                    "step": 0.1
                }),
                "scale": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.01,
                    "max": 10.0,
                    "step": 0.01
                }),
                "translate_x": ("INT", {
                    "default": 0,
                    "min": -8192,
                    "max": 8192,
                    "step": 1
                }),
                "translate_y": ("INT", {
                    "default": 0,
                    "min": -8192,
                    "max": 8192,
                    "step": 1
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
        angle: float = 0.0,
        scale: float = 1.0,
        translate_x: int = 0,
        translate_y: int = 0
    ) -> Tuple[torch.Tensor]:
        """
        Apply combined transform.

        Args:
            image: Input image tensor
            angle: Rotation angle
            scale: Scale factor
            translate_x: Horizontal translation
            translate_y: Vertical translation

        Returns:
            Tuple containing the transformed image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            result = pil_image

            # Apply scale
            if scale != 1.0:
                width, height = result.size
                new_size = (int(width * scale), int(height * scale))
                result = result.resize(new_size, Image.LANCZOS)

            # Apply rotation
            if angle != 0:
                result = result.rotate(angle, resample=Image.BICUBIC, expand=False)

            # Apply translation
            if translate_x != 0 or translate_y != 0:
                # Create a new image with same size, paste translated
                width, height = result.size
                translated = Image.new('RGB', (width, height), (0, 0, 0))
                translated.paste(result, (translate_x, translate_y))
                result = translated

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Transform Error: {str(e)}")
            return (image,)  # Return original on error
