"""
Image processing utilities for Isekai ComfyUI Custom Nodes
"""

import io

import numpy as np
import torch
from PIL import Image


def tensor_to_pil(tensor: torch.Tensor) -> Image.Image:
    """
    Convert ComfyUI IMAGE tensor to PIL Image.

    ComfyUI uses tensors with shape [B, H, W, C] where:
    - B: Batch size
    - H: Height
    - W: Width
    - C: Channels (3 for RGB)
    Values are float32 in range [0.0, 1.0]

    Args:
        tensor: ComfyUI IMAGE tensor [B,H,W,C] or [H,W,C], dtype=float32, range=[0.0,1.0]

    Returns:
        PIL Image in RGB mode

    Example:
        >>> tensor = torch.rand(1, 512, 512, 3)
        >>> pil_image = tensor_to_pil(tensor)
        >>> isinstance(pil_image, Image.Image)
        True
    """
    # Handle batch dimension - take first image if batched
    if len(tensor.shape) == 4:
        tensor = tensor[0]

    # Convert to numpy array on CPU
    image_np = tensor.cpu().numpy()

    # Scale from [0.0, 1.0] to [0, 255] and convert to uint8
    image_np = (image_np * 255).clip(0, 255).astype(np.uint8)

    # Create PIL Image from numpy array
    pil_image = Image.fromarray(image_np, mode='RGB')

    return pil_image


def pil_to_bytes(pil_image: Image.Image, format: str = 'PNG') -> io.BytesIO:
    """
    Encode PIL Image to bytes buffer.

    Args:
        pil_image: PIL Image to encode
        format: Image format (default: 'PNG'). Options: 'PNG', 'JPEG', 'WEBP'

    Returns:
        BytesIO buffer containing encoded image data

    Example:
        >>> from PIL import Image
        >>> img = Image.new('RGB', (100, 100), color='red')
        >>> buffer = pil_to_bytes(img)
        >>> buffer.tell() > 0
        True
    """
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format, optimize=True)
    buffer.seek(0)
    return buffer


def tensor_to_bytes(tensor: torch.Tensor, format: str = 'PNG') -> io.BytesIO:
    """
    Convert ComfyUI IMAGE tensor directly to bytes buffer.

    Convenience function that combines tensor_to_pil and pil_to_bytes.

    Args:
        tensor: ComfyUI IMAGE tensor [B,H,W,C] or [H,W,C]
        format: Image format (default: 'PNG')

    Returns:
        BytesIO buffer containing encoded image data

    Example:
        >>> tensor = torch.rand(1, 512, 512, 3)
        >>> buffer = tensor_to_bytes(tensor)
        >>> buffer.tell() > 0
        True
    """
    pil_image = tensor_to_pil(tensor)
    return pil_to_bytes(pil_image, format=format)
