"""
Isekai Split Toning Node for ComfyUI

Applies different colors to highlights and shadows.
"""

from typing import Tuple
import torch
import numpy as np
from PIL import Image

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiSplitToning:
    """
    Split toning effect.

    Applies different color tints to highlights and shadows separately.
    Common technique in color grading.

    Category: Isekai/Image/Blend
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "highlight_color": (["Warm", "Cool", "Yellow", "Blue", "Red", "Green"],),
                "shadow_color": (["Warm", "Cool", "Yellow", "Blue", "Red", "Green"],),
            },
            "optional": {
                "intensity": ("FLOAT", {
                    "default": 0.3,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "display": "slider"
                }),
                "balance": ("FLOAT", {
                    "default": 0.5,
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
        highlight_color: str,
        shadow_color: str,
        intensity: float = 0.3,
        balance: float = 0.5
    ) -> Tuple[torch.Tensor]:
        """
        Apply split toning.

        Args:
            image: Input image tensor
            highlight_color: Color for highlights
            shadow_color: Color for shadows
            intensity: Toning intensity
            balance: Highlight/shadow balance

        Returns:
            Tuple containing the toned image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Convert to numpy
            img_array = np.array(pil_image).astype(np.float32)

            # Define color tints (R, G, B)
            colors = {
                "Warm": np.array([255, 200, 150]),
                "Cool": np.array([150, 200, 255]),
                "Yellow": np.array([255, 255, 0]),
                "Blue": np.array([0, 100, 255]),
                "Red": np.array([255, 100, 100]),
                "Green": np.array([100, 255, 100])
            }

            highlight_tint = colors.get(highlight_color, colors["Warm"])
            shadow_tint = colors.get(shadow_color, colors["Cool"])

            # Calculate luminance
            luminance = np.dot(img_array, [0.299, 0.587, 0.114])

            # Create masks for highlights and shadows
            highlight_mask = (luminance / 255.0) > balance
            shadow_mask = ~highlight_mask

            # Apply tints
            result_array = img_array.copy()

            # Tint highlights
            for c in range(3):
                tint_amount = intensity * highlight_mask
                result_array[:, :, c] = result_array[:, :, c] * (1 - tint_amount) + highlight_tint[c] * tint_amount

            # Tint shadows
            for c in range(3):
                tint_amount = intensity * shadow_mask
                result_array[:, :, c] = result_array[:, :, c] * (1 - tint_amount) + shadow_tint[c] * tint_amount

            result_array = np.clip(result_array, 0, 255).astype(np.uint8)
            result = Image.fromarray(result_array)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Split Toning Error: {str(e)}")
            return (image,)  # Return original on error
