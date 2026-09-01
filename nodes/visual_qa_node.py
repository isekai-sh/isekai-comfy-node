"""ComfyUI node for deterministic, local multimodal visual QA."""

import json
from io import BytesIO
from typing import Any, Dict, List, Tuple

import torch

try:
    from ..utils.image_utils import pil_to_bytes, tensor_to_pil
    from ..utils.ollama_vision_client import (
        DEFAULT_VISION_MODEL,
        evaluate_image_with_ollama,
    )
except (ImportError, ValueError):
    from utils.image_utils import pil_to_bytes, tensor_to_pil
    from utils.ollama_vision_client import (
        DEFAULT_VISION_MODEL,
        evaluate_image_with_ollama,
    )


DEFAULT_VISUAL_QA_RUBRIC = """Evaluate whether this AI-generated artwork is ready to publish.

Anatomy:
- Check hands and fingers for wrong counts, fused digits, malformed joints, or impossible grips.
- Check limbs, shoulders, torso, neck, ears, eyes, teeth, and facial symmetry for distortion.
- Check body proportions, pose continuity, duplicated anatomy, and impossible merges or intersections.

Artifacts:
- Check for duplicated or missing features, warped geometry, floating objects, accidental cutoffs, and broken edges.
- Check for unintended text, signatures, watermarks, UI fragments, seams, tiling, halos, banding, noise, and upscale or compression artifacts.
- Check detailed backgrounds and accessories for melting, repetition, or inconsistent perspective.

Composition and finish:
- Check subject legibility, crop, focus, exposure, contrast, color consistency, and obviously unfinished regions.

Blocking issues include a broken primary face or hands, severe anatomy failure, prominent unintended text or watermark, major duplication or merging, or corrupted or blank output.

Judge technical image quality only. Do not reject subject matter, mature content, artistic taste, or intentional stylization."""

QA_VIEW_MAX_EDGE = 1024


def _try_unload_comfy_models() -> List[str]:
    """Best-effort VRAM release without making QA depend on Comfy internals."""
    try:
        import comfy.model_management as model_management
    except (ImportError, ModuleNotFoundError):
        return ["Comfy model management is unavailable; inference continued without unloading."]

    try:
        model_management.unload_all_models()
        model_management.soft_empty_cache()
    except Exception as exc:
        return [f"Could not unload Comfy models: {exc}"]
    return []


def _batch_images(image: torch.Tensor) -> List[torch.Tensor]:
    shape = getattr(image, "shape", None)
    if shape is None:
        raise ValueError("IMAGE input does not expose a tensor shape.")
    if len(shape) == 3:
        return [image]
    if len(shape) == 4 and int(shape[0]) > 0:
        return [image[index] for index in range(int(shape[0]))]
    raise ValueError("IMAGE input must have shape [H,W,C] or non-empty [B,H,W,C].")


def _fit_qa_view(pil_image: Any) -> Any:
    """Bound a QA view so five-view requests fit the configured model context."""
    view = pil_image.copy()
    if max(view.size) > QA_VIEW_MAX_EDGE:
        from PIL import Image

        view.thumbnail(
            (QA_VIEW_MAX_EDGE, QA_VIEW_MAX_EDGE),
            Image.Resampling.LANCZOS,
        )
    return view


def _qa_image_views(pil_image: Any) -> List[BytesIO]:
    """Encode a bounded full frame and four bounded quadrant detail crops."""
    width, height = pil_image.size
    if width < 2 or height < 2:
        return [pil_to_bytes(_fit_qa_view(pil_image), format="PNG", optimize=True)]

    split_x = width // 2
    split_y = height // 2
    boxes = [
        (0, 0, split_x, split_y),
        (split_x, 0, width, split_y),
        (0, split_y, split_x, height),
        (split_x, split_y, width, height),
    ]
    views = [_fit_qa_view(pil_image)] + [
        _fit_qa_view(pil_image.crop(box)) for box in boxes
    ]
    return [pil_to_bytes(view, format="PNG", optimize=True) for view in views]


class IsekaiVisualQA:
    """Review generated images locally and return a deterministic publish gate."""

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "image": ("IMAGE",),
                "model": ("STRING", {
                    "default": DEFAULT_VISION_MODEL,
                    "multiline": False,
                    "placeholder": "qwen3-vl:8b",
                }),
                "ollama_url": ("STRING", {
                    "default": "http://localhost:11434",
                    "multiline": False,
                }),
                "rubric": ("STRING", {
                    "default": DEFAULT_VISUAL_QA_RUBRIC,
                    "multiline": True,
                }),
                "approval_threshold": ("INT", {
                    "default": 80,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "display": "slider",
                }),
                "unload_comfy_models": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Release ComfyUI models from VRAM before Ollama vision inference.",
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "BOOLEAN", "INT", "STRING")
    RETURN_NAMES = ("image", "approved", "score", "report_json")
    FUNCTION = "evaluate"
    CATEGORY = "Isekai/LLMs"

    def evaluate(
        self,
        image: torch.Tensor,
        model: str = DEFAULT_VISION_MODEL,
        ollama_url: str = "http://localhost:11434",
        rubric: str = DEFAULT_VISUAL_QA_RUBRIC,
        approval_threshold: int = 80,
        unload_comfy_models: bool = True,
    ) -> Tuple[torch.Tensor, bool, int, str]:
        threshold = max(0, min(100, int(approval_threshold)))
        rubric = (rubric or "").strip() or DEFAULT_VISUAL_QA_RUBRIC
        runtime_warnings = _try_unload_comfy_models() if unload_comfy_models else []

        try:
            batch = _batch_images(image)
        except (TypeError, ValueError) as exc:
            return self._failure_result(
                image, threshold, model, runtime_warnings, str(exc)
            )

        image_reports: List[Dict[str, Any]] = []
        try:
            for index, image_tensor in enumerate(batch):
                pil_image = tensor_to_pil(image_tensor)
                image_views = _qa_image_views(pil_image)
                model_report = evaluate_image_with_ollama(
                    image_bytes=image_views,
                    model=model,
                    rubric=rubric,
                    base_url=ollama_url,
                )
                blocking_issues = model_report["blocking_issues"]
                image_reports.append({
                    "batch_index": index,
                    "width": pil_image.width,
                    "height": pil_image.height,
                    "approved": (
                        model_report["score"] >= threshold
                        and len(blocking_issues) == 0
                    ),
                    **model_report,
                })
        except Exception as exc:
            return self._failure_result(
                image, threshold, model, runtime_warnings, str(exc)
            )

        score = min(report["score"] for report in image_reports)
        model_score = min(report["model_score"] for report in image_reports)
        blocking_issues = [
            {"batch_index": report["batch_index"], **issue}
            for report in image_reports
            for issue in report["blocking_issues"]
        ]
        approved = score >= threshold and len(blocking_issues) == 0
        report = {
            "approved": approved,
            "score": score,
            "model_score": model_score,
            "threshold": threshold,
            "model": (model or "").strip(),
            "batch_size": len(image_reports),
            "blocking_issues": blocking_issues,
            "runtime_warnings": runtime_warnings,
            "images": image_reports,
        }
        return image, approved, score, json.dumps(
            report, ensure_ascii=False, indent=2, sort_keys=True
        )

    def _failure_result(
        self,
        image: torch.Tensor,
        threshold: int,
        model: str,
        runtime_warnings: List[str],
        error: str,
    ) -> Tuple[torch.Tensor, bool, int, str]:
        blocking_issue = {
            "severity": "blocking",
            "category": "inference_error",
            "description": error or "Visual QA failed.",
            "location": "visual_qa",
        }
        report = {
            "approved": False,
            "score": 0,
            "model_score": None,
            "threshold": threshold,
            "model": (model or "").strip(),
            "batch_size": 0,
            "blocking_issues": [blocking_issue],
            "runtime_warnings": runtime_warnings,
            "images": [],
        }
        return image, False, 0, json.dumps(
            report, ensure_ascii=False, indent=2, sort_keys=True
        )
