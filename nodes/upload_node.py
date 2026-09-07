"""
Isekai Upload Node for ComfyUI

This module provides functionality to upload generated images directly to the Isekai platform.
"""

import json
import os
from datetime import datetime
from typing import Tuple, Dict, Any

import requests
import torch

# Try relative imports first (production), fall back to absolute
try:
    from ..config import get_api_url
    from ..utils.validation import validate_api_key, validate_title, sanitize_filename
    from ..utils.image_utils import tensor_to_pil, pil_to_bytes
    from .base import IsekaiUploadError
except (ImportError, ValueError):
    from config import get_api_url
    from utils.validation import validate_api_key, validate_title, sanitize_filename
    from utils.image_utils import tensor_to_pil, pil_to_bytes
    from nodes.base import IsekaiUploadError


SUBMISSION_POLICY_MANUAL_REVIEW = "Manual review"
SUBMISSION_POLICY_DIRECT_TO_DRAFT = "Direct to draft"
SUBMISSION_POLICY_USE_QA_DECISION = "Use QA decision"
SUBMISSION_POLICY_OPTIONS = [
    SUBMISSION_POLICY_MANUAL_REVIEW,
    SUBMISSION_POLICY_DIRECT_TO_DRAFT,
    SUBMISSION_POLICY_USE_QA_DECISION,
]
SUBMISSION_POLICY_VALUES = {
    SUBMISSION_POLICY_MANUAL_REVIEW.casefold(): "manual_review",
    SUBMISSION_POLICY_DIRECT_TO_DRAFT.casefold(): "direct_to_draft",
    "manual_review": "manual_review",
    "direct_to_draft": "direct_to_draft",
}
QA_UNAVAILABLE_REASON = (
    "Automated QA could not complete the review. Please review this image manually."
)


class IsekaiUploadNode:
    """
    ComfyUI custom node for uploading images to Isekai platform.

    This node takes an image tensor from ComfyUI, converts it to PNG format,
    and uploads it to the Isekai API with metadata (title and tags). The image
    is returned unchanged to allow pass-through to preview nodes.

    Attributes:
        RETURN_TYPES: Tuple containing ("IMAGE",)
        FUNCTION: "upload"
        CATEGORY: "Isekai"
        OUTPUT_NODE: True (enables preview functionality)

    Example:
        This node is typically connected in a workflow like:
        VAE Decode -> Isekai Upload -> Preview Image
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input parameters for the node.

        Returns:
            Dictionary containing required and optional input specifications:
            - image: ComfyUI IMAGE tensor
            - title: Upload title (required, max 200 characters)
            - api_key: Isekai API key (optional, uses ISEKAI_API_KEY env var if not provided)
            - api_url: Isekai API base URL (optional, uses ISEKAI_API_URL env var or defaults to https://api.isekai.sh)
            - tags: Comma-separated tags (optional)
            - format: Image format - JPEG or PNG (optional, default: JPEG)
            - quality: Compression quality 1-100 (optional, default: 90)
            - submission_policy: Whether the upload requires manual review or goes directly to a draft
            - qa_approved: Optional QA decision input used only by "Use QA decision"
        """
        return {
            "required": {
                "image": ("IMAGE",),
                "title": ("STRING", {
                    "default": "ComfyUI Upload",
                    "multiline": False,
                }),
            },
            "optional": {
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Leave empty to use ISEKAI_API_KEY environment variable"
                }),
                "api_url": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "https://your.isekai.run"
                }),
                "tags": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "tag1, tag2, tag3"
                }),
                "format": (["JPEG", "PNG"], {
                    "default": "JPEG"
                }),
                "quality": ("INT", {
                    "default": 90,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "slider"
                }),
                "submission_policy": (SUBMISSION_POLICY_OPTIONS, {
                    "default": SUBMISSION_POLICY_MANUAL_REVIEW,
                    "tooltip": "Manual review is the safe default. Direct to draft skips the review queue. Use QA decision follows the qa_approved input."
                }),
                # Append new inputs to preserve widget ordering in saved workflows.
                "qa_approved": ("BOOLEAN", {
                    "default": False,
                    "forceInput": True,
                    "tooltip": "Used only with Use QA decision. Missing or false keeps the upload in manual review."
                }),
                "generation_run_id": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Injected by Isekai Core for managed generation runs."
                }),
                "generation_output_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "Injected by Isekai Core to make the upload idempotent."
                }),
                "qa_report": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "forceInput": True,
                    "tooltip": "Connect the Visual QA report output so Core can show review reasons."
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "upload"
    CATEGORY = "Isekai/Upload"
    OUTPUT_NODE = True

    def _get_api_key(self, api_key_input: str = "") -> str:
        """
        Get API key from input or environment variable.

        Priority:
        1. Environment variable ISEKAI_API_KEY (recommended, more secure)
        2. Node input api_key parameter (fallback)

        Args:
            api_key_input: API key from node input (optional)

        Returns:
            API key string

        Raises:
            IsekaiUploadError: If no API key found in either location
        """
        # Check environment variable first (more secure)
        env_key = os.environ.get("ISEKAI_API_KEY", "").strip()

        if env_key:
            print("[Isekai] Using API key from ISEKAI_API_KEY environment variable")
            return env_key

        # Fall back to node input
        if api_key_input and api_key_input.strip():
            print("[Isekai] Using API key from node input (consider using ISEKAI_API_KEY env var instead)")
            return api_key_input.strip()

        # No API key found
        raise IsekaiUploadError(
            "No API key provided. Either:\n"
            "1. Set ISEKAI_API_KEY environment variable (recommended), or\n"
            "2. Enter API key in the node's api_key field"
        )

    def _get_api_url(self, api_url_input: str = "") -> str:
        """
        Get API base URL from input, environment variable, or default.

        Priority:
        1. Node input api_url parameter (for flexibility with self-hosted instances)
        2. Environment variable ISEKAI_API_URL (fallback)
        3. Default URL https://api.isekai.sh (final fallback)

        Args:
            api_url_input: API URL from node input (optional)

        Returns:
            API base URL string (without trailing slash)
        """
        # Check node input first (allows per-workflow configuration)
        if api_url_input and api_url_input.strip():
            url = api_url_input.strip().rstrip('/')
            print(f"[Isekai] Using API URL from node input: {url}")
            return url

        # Fall back to environment variable
        env_url = os.environ.get("ISEKAI_API_URL", "").strip()
        if env_url:
            url = env_url.rstrip('/')
            print(f"[Isekai] Using API URL from ISEKAI_API_URL environment variable: {url}")
            return url

        # Use default URL
        url = get_api_url().rstrip('/')
        print(f"[Isekai] Using default API URL: {url}")
        return url

    def _get_save_kwargs(self, format: str, quality: int) -> dict:
        """
        Get PIL Image.save() kwargs for compression based on format and quality.

        Args:
            format: Image format ('PNG', 'JPEG')
            quality: Quality value (1-100)

        Returns:
            Dictionary of kwargs to pass to Image.save()
        """
        if format == "PNG":
            # PNG uses compress_level (0-9), quality is ignored
            # Map quality 1-100 to compress_level 9-0 (higher quality = lower compression)
            compress_level = max(0, min(9, int((100 - quality) / 11)))
            return {"compress_level": compress_level, "optimize": True}
        else:  # JPEG
            return {"quality": quality, "optimize": True}

    def _get_review_policy(
        self,
        submission_policy: str = SUBMISSION_POLICY_MANUAL_REVIEW,
        qa_approved: bool = False,
    ) -> str:
        """Convert the user-facing submission policy to its API wire value.

        Missing and unknown values fail closed to manual review. This keeps
        workflows saved before the widget existed backward compatible without
        allowing them to bypass review accidentally.
        """
        normalized = str(submission_policy or "").strip().casefold()

        if normalized == SUBMISSION_POLICY_USE_QA_DECISION.casefold():
            return "direct_to_draft" if qa_approved is True else "manual_review"

        review_policy = SUBMISSION_POLICY_VALUES.get(normalized)

        if review_policy is None:
            print(
                f"[Isekai] Unknown submission policy '{submission_policy}'. "
                "Falling back to Manual review."
            )
            return "manual_review"

        return review_policy

    def _summarize_qa_report(self, qa_report: str, qa_approved: bool) -> str:
        """Reduce the internal QA report to safe, bounded review context for Core."""
        raw_report = str(qa_report or "").strip()
        if not raw_report:
            return ""

        try:
            report = json.loads(raw_report)
        except (TypeError, ValueError):
            report = {}

        if not isinstance(report, dict):
            report = {}

        reasons = []
        issues = report.get("blocking_issues", [])
        if isinstance(issues, list):
            for issue in issues[:12]:
                if not isinstance(issue, dict):
                    continue
                text = str(issue.get("description") or issue.get("text") or "").strip()
                if not text:
                    continue
                category = str(issue.get("category") or "").strip()
                location = str(issue.get("location") or "").strip()
                if category.casefold() == "inference_error":
                    text = QA_UNAVAILABLE_REASON
                    category = "qa_unavailable"
                    location = ""
                reason = {"text": text[:500]}
                if category:
                    reason["category"] = category[:100]
                if location:
                    reason["location"] = location[:100]
                reasons.append(reason)

        approved = report.get("approved")
        if not isinstance(approved, bool):
            approved = qa_approved is True
        if not approved and not reasons:
            reasons.append({"text": "Visual QA did not approve this image."})

        score = report.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            score = None

        summary = {
            "source": "visual_qa",
            "approved": approved,
            "score": score,
            "reasons": reasons,
        }
        return json.dumps(summary, ensure_ascii=False, separators=(",", ":"))

    def upload(
        self,
        image: torch.Tensor,
        title: str,
        api_key: str = "",
        api_url: str = "",
        tags: str = "",
        format: str = "JPEG",
        quality: int = 90,
        submission_policy: str = SUBMISSION_POLICY_MANUAL_REVIEW,
        qa_approved: bool = False,
        generation_run_id: str = "",
        generation_output_key: str = "",
        qa_report: str = "",
    ) -> Tuple[torch.Tensor]:
        """
        Upload image to Isekai platform with metadata and compression.

        Args:
            image: ComfyUI IMAGE tensor [B,H,W,C], float32, range [0.0,1.0]
            title: Upload title (max 200 characters, will be truncated if longer)
            api_key: Isekai API key (optional, uses ISEKAI_API_KEY env var if empty)
            api_url: Isekai API base URL (optional, uses ISEKAI_API_URL env var or defaults to https://api.isekai.sh)
            tags: Comma-separated tags (optional)
            format: Image format for upload ('JPEG' or 'PNG', default: 'JPEG')
            quality: Compression quality 1-100 (default: 90)
                    - For JPEG: Direct quality parameter (90 = excellent quality)
                    - For PNG: Mapped to compress_level (higher quality = less compression)
            submission_policy: "Manual review" (default), "Direct to draft", or "Use QA decision"
            qa_approved: QA decision for "Use QA decision"; missing/false defaults to manual review
            generation_run_id: Core-managed run identifier (normally injected automatically)
            generation_output_key: Core-managed idempotency key (normally injected automatically)
            qa_report: Visual QA report used to show concise review reasons in Core

        Returns:
            Tuple containing the input image unchanged (pass-through for preview)

        Raises:
            IsekaiUploadError: If validation fails or upload errors occur

        Example:
            >>> node = IsekaiUploadNode()
            >>> image_tensor = torch.rand(1, 512, 512, 3)
            >>> # Using environment variable (recommended)
            >>> os.environ["ISEKAI_API_KEY"] = "isk_" + "a"*64
            >>> result = node.upload(image_tensor, "My Image")
            >>> result[0] is image_tensor
            True
        """
        try:
            # Get API key from environment variable or input
            api_key = self._get_api_key(api_key)

            # Get API URL from node input, environment variable, or default
            api_url = self._get_api_url(api_url)

            # Validate API key
            is_valid, error_msg = validate_api_key(api_key)
            if not is_valid:
                raise IsekaiUploadError(error_msg)

            # Validate and sanitize title
            is_valid, sanitized_title, warning_msg = validate_title(title)
            if not is_valid:
                raise IsekaiUploadError(warning_msg)

            if warning_msg:
                print(f"[Isekai] Warning: {warning_msg}")

            # Convert the UI label to the API wire value. Unknown values fail
            # closed to manual review for backward compatibility and safety.
            review_policy = self._get_review_policy(submission_policy, qa_approved)

            # Convert tensor to PIL Image
            print("[Isekai] Converting image tensor to PIL Image...")
            pil_image = tensor_to_pil(image)

            # Get compression settings
            save_kwargs = self._get_save_kwargs(format, quality)

            # Encode with compression
            print(f"[Isekai] Encoding image as {format} with quality={quality}...")
            print(f"[Isekai] Compression settings: {save_kwargs}")
            image_bytes = pil_to_bytes(pil_image, format=format, **save_kwargs)

            # Log compressed size
            compressed_size_kb = len(image_bytes.getvalue()) / 1024
            print(f"[Isekai] Compressed image size: {compressed_size_kb:.2f} KB")

            # Generate filename with correct extension
            filename = self._generate_filename(sanitized_title, format)

            # Prepare metadata
            metadata = {
                "title": sanitized_title,
                "tags": tags,
                "reviewPolicy": review_policy,
                "generationRunId": generation_run_id.strip(),
                "generationOutputKey": generation_output_key.strip(),
                "generationQa": self._summarize_qa_report(qa_report, qa_approved),
            }

            # Upload to Isekai
            print(
                f"[Isekai] Uploading '{sanitized_title}' to Isekai "
                f"with reviewPolicy={review_policy}..."
            )
            result = self._upload_to_isekai(image_bytes, filename, api_key, api_url, metadata, format)

            # Success message
            deviation_id = result.get("deviationId")
            status = result.get("status")
            message = result.get("message", "Upload successful")
            print(f"[Isekai] {message}")
            print(f"[Isekai] Deviation ID: {deviation_id}, Status: {status}")

            # Return input image unchanged (pass-through)
            return (image,)

        except IsekaiUploadError:
            raise
        except Exception as e:
            raise IsekaiUploadError(f"Unexpected error during upload: {str(e)}")

    def _generate_filename(self, title: str, format: str = "PNG") -> str:
        """
        Generate a safe filename from title with timestamp and format extension.

        Args:
            title: Title string to use for filename
            format: Image format ('PNG' or 'JPEG')

        Returns:
            Safe filename with format: sanitized_title_YYYYMMDD_HHMMSS.{ext}
        """
        safe_title = sanitize_filename(title, max_length=100)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = "jpg" if format == "JPEG" else "png"
        filename = f"{safe_title}_{timestamp}.{extension}"
        return filename

    def _upload_to_isekai(
        self,
        image_bytes: bytes,
        filename: str,
        api_key: str,
        api_url: str,
        metadata: Dict[str, str],
        format: str = "PNG"
    ) -> Dict[str, Any]:
        """
        Upload image and metadata to Isekai API.

        Args:
            image_bytes: Image data as bytes
            filename: Filename for the upload
            api_key: Isekai API key
            api_url: Isekai API base URL
            metadata: Dictionary containing title and tags
            format: Image format ('PNG' or 'JPEG')

        Returns:
            API response as dictionary

        Raises:
            IsekaiUploadError: If upload fails
        """
        upload_url = f"{api_url}/api/comfyui/upload"

        # Determine content type based on format
        content_type = "image/jpeg" if format == "JPEG" else "image/png"

        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"file": (filename, image_bytes, content_type)}
        data = {
            "title": metadata["title"][:200],
            "isAiGenerated": "true",
            # Default here as well so direct/internal callers remain safe.
            "reviewPolicy": metadata.get("reviewPolicy", "manual_review"),
        }

        # Add tags if provided
        if metadata.get("tags"):
            tags_list = [t.strip() for t in metadata["tags"].split(",") if t.strip()]
            if tags_list:
                data["tags"] = json.dumps(tags_list)

        if metadata.get("generationRunId"):
            data["generationRunId"] = metadata["generationRunId"]
        if metadata.get("generationOutputKey"):
            data["generationOutputKey"] = metadata["generationOutputKey"]
        if metadata.get("generationQa"):
            data["generationQa"] = metadata["generationQa"]

        try:
            response = requests.post(
                upload_url,
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )

            # Handle various HTTP status codes
            if response.status_code == 401:
                raise IsekaiUploadError("Authentication failed. Invalid or revoked API key.")
            elif response.status_code == 403:
                raise IsekaiUploadError("Storage limit exceeded.")
            elif response.status_code == 429:
                raise IsekaiUploadError("Rate limit exceeded. Please wait before uploading again.")
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", f"HTTP {response.status_code}")
                except Exception:
                    error_msg = f"HTTP {response.status_code}"
                raise IsekaiUploadError(f"Upload failed: {error_msg}")

            return response.json()

        except requests.exceptions.Timeout:
            raise IsekaiUploadError("Upload request timed out after 60 seconds.")
        except requests.exceptions.ConnectionError:
            raise IsekaiUploadError(f"Failed to connect to Isekai API at {api_url}.")
        except IsekaiUploadError:
            raise
        except Exception as e:
            raise IsekaiUploadError(f"Unexpected error during upload: {str(e)}")
