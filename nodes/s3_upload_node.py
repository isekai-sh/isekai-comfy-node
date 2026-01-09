"""
Isekai S3 Upload Node for ComfyUI

This module provides functionality to upload generated images to AWS S3
and S3-compatible services (Cloudflare R2, DigitalOcean Spaces, Backblaze B2,
MinIO, Wasabi, Linode Object Storage, etc.).
"""

from typing import Tuple, Dict, Any
from datetime import datetime

import torch

# Try relative imports first (production), fall back to absolute
try:
    from ..utils.s3_client import (
        get_s3_credentials,
        upload_to_s3_http,
        generate_s3_url,
        S3UploadError
    )
    from ..utils.image_utils import tensor_to_pil, pil_to_bytes
    from ..utils.validation import sanitize_filename
except (ImportError, ValueError):
    from utils.s3_client import (
        get_s3_credentials,
        upload_to_s3_http,
        generate_s3_url,
        S3UploadError
    )
    from utils.image_utils import tensor_to_pil, pil_to_bytes
    from utils.validation import sanitize_filename


class IsekaiS3Upload:
    """
    Upload images to S3-compatible storage services.

    Supports AWS S3 and all S3-compatible services including Cloudflare R2,
    DigitalOcean Spaces, Backblaze B2, MinIO, Wasabi, and Linode Object Storage.

    Uses HTTP requests with AWS Signature Version 4 authentication - no boto3 required.

    Attributes:
        RETURN_TYPES: Tuple containing ("IMAGE", "STRING")
        RETURN_NAMES: Tuple containing ("image", "url")
        FUNCTION: "upload"
        CATEGORY: "Isekai/Upload"
        OUTPUT_NODE: True (enables preview functionality)

    Example:
        This node is typically connected in a workflow like:
        VAE Decode -> S3 Upload -> Preview Image
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required and optional input specifications:
            - image: ComfyUI IMAGE tensor (required)
            - bucket_name: S3 bucket name (required)
            - object_key: Object key/path in bucket (required)
            - access_key_id: AWS access key ID (optional, uses env var if not provided)
            - secret_access_key: AWS secret access key (optional, uses env var if not provided)
            - region: AWS region or S3-compatible region (optional)
            - endpoint_url: Custom endpoint for S3-compatible services (optional)
            - format: Image format - JPEG, PNG, or WEBP (optional)
            - quality: Compression quality 1-100 (optional)
            - acl: Access control list (optional)
        """
        return {
            "required": {
                "image": ("IMAGE",),
                "bucket_name": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "your-bucket-name"
                }),
                "object_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "images/output.jpg"
                }),
            },
            "optional": {
                "access_key_id": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "⚠️ Use AWS_ACCESS_KEY_ID env var instead"
                }),
                "secret_access_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "⚠️ Use AWS_SECRET_ACCESS_KEY env var instead"
                }),
                "region": ("STRING", {
                    "default": "us-east-1",
                    "multiline": False,
                    "placeholder": "us-east-1"
                }),
                "endpoint_url": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Leave empty for AWS S3, or enter custom endpoint URL"
                }),
                "format": (["JPEG", "PNG", "WEBP"],),
                "quality": ("INT", {
                    "default": 90,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "slider"
                }),
                "acl": ([
                    "private",
                    "public-read",
                    "public-read-write",
                    "authenticated-read"
                ],),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "url")
    FUNCTION = "upload"
    CATEGORY = "Isekai/Upload"
    OUTPUT_NODE = True

    def _get_content_type(self, format: str) -> str:
        """
        Map image format to MIME content type.

        Args:
            format: Image format ('JPEG', 'PNG', 'WEBP')

        Returns:
            MIME type string
        """
        mapping = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "WEBP": "image/webp"
        }
        return mapping.get(format, "application/octet-stream")

    def _get_save_kwargs(self, format: str, quality: int) -> dict:
        """
        Get PIL Image.save() kwargs for compression based on format and quality.

        Args:
            format: Image format ('PNG', 'JPEG', 'WEBP')
            quality: Quality value (1-100)

        Returns:
            Dictionary of kwargs to pass to Image.save()
        """
        if format == "PNG":
            # PNG uses compress_level (0-9), quality is ignored
            # Map quality 1-100 to compress_level 9-0 (higher quality = lower compression)
            compress_level = max(0, min(9, int((100 - quality) / 11)))
            return {"compress_level": compress_level, "optimize": True}
        elif format == "WEBP":
            return {"quality": quality, "method": 6}
        else:  # JPEG
            return {"quality": quality, "optimize": True}

    def _generate_filename(self, object_key: str, format: str) -> str:
        """
        Generate filename from object key with correct extension.

        If object_key has no extension, adds one based on format.
        If object_key has extension, uses it as-is.

        Args:
            object_key: Object key/path from user input
            format: Image format ('PNG', 'JPEG', 'WEBP')

        Returns:
            Object key with proper extension
        """
        # Check if object_key already has an extension
        if "." in object_key.split("/")[-1]:
            return object_key

        # Add extension based on format
        extension = "jpg" if format == "JPEG" else format.lower()
        return f"{object_key}.{extension}"

    def upload(
        self,
        image: torch.Tensor,
        bucket_name: str,
        object_key: str,
        access_key_id: str = "",
        secret_access_key: str = "",
        region: str = "us-east-1",
        endpoint_url: str = "",
        format: str = "JPEG",
        quality: int = 90,
        acl: str = "private"
    ) -> Tuple[torch.Tensor, str]:
        """
        Upload image to S3 or S3-compatible storage service.

        Args:
            image: ComfyUI IMAGE tensor [B,H,W,C], float32, range [0.0,1.0]
            bucket_name: S3 bucket name
            object_key: Object key/path in bucket (e.g., "images/output.jpg")
            access_key_id: AWS access key ID (optional, uses AWS_ACCESS_KEY_ID env var if empty)
            secret_access_key: AWS secret access key (optional, uses AWS_SECRET_ACCESS_KEY env var if empty)
            region: AWS region or S3-compatible region (default: "us-east-1")
            endpoint_url: Custom endpoint URL for S3-compatible services (empty for AWS S3)
            format: Image format for upload ('JPEG', 'PNG', or 'WEBP', default: 'JPEG')
            quality: Compression quality 1-100 (default: 90)
            acl: Access control list (default: "private")

        Returns:
            Tuple containing:
            - Input image unchanged (pass-through for preview)
            - S3 URL to uploaded object

        Raises:
            S3UploadError: If validation fails or upload errors occur

        Example:
            >>> node = IsekaiS3Upload()
            >>> image_tensor = torch.rand(1, 512, 512, 3)
            >>> os.environ["AWS_ACCESS_KEY_ID"] = "AKIAIOSFODNN7EXAMPLE"
            >>> os.environ["AWS_SECRET_ACCESS_KEY"] = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            >>> result = node.upload(image_tensor, "my-bucket", "images/test.jpg")
            >>> result[0] is image_tensor
            True
            >>> "https://" in result[1]
            True
        """
        try:
            # Validate required inputs
            if not bucket_name or not bucket_name.strip():
                raise S3UploadError("Bucket name is required")

            if not object_key or not object_key.strip():
                raise S3UploadError("Object key is required")

            bucket_name = bucket_name.strip()
            object_key = object_key.strip()

            # Add extension if not present
            object_key = self._generate_filename(object_key, format)

            # Get credentials with security warnings
            access_key, secret_key = get_s3_credentials(
                access_key_id, secret_access_key
            )

            # Convert tensor to PIL Image
            print("[Isekai] S3: Converting image tensor to PIL Image...")
            pil_image = tensor_to_pil(image)

            # Get compression settings
            save_kwargs = self._get_save_kwargs(format, quality)

            # Encode with compression
            print(f"[Isekai] S3: Encoding image as {format} with quality={quality}...")
            print(f"[Isekai] S3: Compression settings: {save_kwargs}")
            image_bytes = pil_to_bytes(pil_image, format=format, **save_kwargs)

            # Log compressed size
            compressed_size_kb = len(image_bytes.getvalue()) / 1024
            print(f"[Isekai] S3: Compressed image size: {compressed_size_kb:.2f} KB")

            # Determine content type
            content_type = self._get_content_type(format)

            # Upload to S3
            service_name = endpoint_url if endpoint_url else f"AWS S3 ({region})"
            print(f"[Isekai] S3: Uploading to {service_name}...")
            print(f"[Isekai] S3: Bucket: {bucket_name}, Key: {object_key}")

            upload_to_s3_http(
                bucket=bucket_name,
                key=object_key,
                file_bytes=image_bytes.getvalue(),
                content_type=content_type,
                acl=acl,
                access_key=access_key,
                secret_key=secret_key,
                region=region,
                endpoint_url=endpoint_url
            )

            # Generate URL
            url = generate_s3_url(bucket_name, object_key, region, endpoint_url)
            print(f"[Isekai] S3: URL: {url}")

            # Return image + URL
            return (image, url)

        except S3UploadError as e:
            print(f"[Isekai] S3 Error: {str(e)}")
            return (image, f"Error: {str(e)}")
        except Exception as e:
            print(f"[Isekai] S3 Unexpected Error: {str(e)}")
            return (image, f"Unexpected error: {str(e)}")
