"""
Isekai Edge Enhance Node for ComfyUI

Enhances edges in images.
"""

from typing import Tuple
import torch
from PIL import ImageFilter

try:
    from ...utils.image_utils import tensor_to_pil, pil_to_tensor
except (ImportError, ValueError):
    from utils.image_utils import tensor_to_pil, pil_to_tensor


class IsekaiEdgeEnhance:
    """
    Enhance image edges.

    Makes edges in the image more pronounced.
    Useful for increasing apparent sharpness and detail.

    Category: Isekai/Image/Effects
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "method": (["Edge Enhance", "Edge Enhance More", "Find Edges"],),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "apply"
    CATEGORY = "Isekai/Image/Effects"

    def apply(self, image: torch.Tensor, method: str) -> Tuple[torch.Tensor]:
        """
        Enhance edges.

        Args:
            image: Input image tensor
            method: Enhancement method

        Returns:
            Tuple containing the edge-enhanced image tensor
        """
        try:
            # Convert tensor to PIL
            pil_image = tensor_to_pil(image)

            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Apply edge enhancement
            if method == "Edge Enhance":
                result = pil_image.filter(ImageFilter.EDGE_ENHANCE)
            elif method == "Edge Enhance More":
                result = pil_image.filter(ImageFilter.EDGE_ENHANCE_MORE)
            else:  # Find Edges
                result = pil_image.filter(ImageFilter.FIND_EDGES)

            # Convert back to tensor
            return (pil_to_tensor(result),)

        except Exception as e:
            print(f"[Isekai] Edge Enhance Error: {str(e)}")
            return (image,)  # Return original on error
