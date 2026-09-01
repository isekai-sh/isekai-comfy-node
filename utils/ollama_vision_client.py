"""Structured local Ollama vision requests for Isekai Visual QA."""

import base64
import json
from io import BytesIO
from typing import Any, Dict, List, Sequence, Union

import requests


DEFAULT_VISION_MODEL = "qwen3-vl:8b"
ImageBytes = Union[bytes, bytearray, BytesIO]

VISUAL_QA_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": (
                "Model's diagnostic technical-quality estimate. The client "
                "recomputes its gate score deterministically from issue severities."
            ),
        },
        "summary": {
            "type": "string",
            "description": "Concise visual quality assessment.",
        },
        "blocking_issues": {
            "type": "array",
            "description": "Issues severe enough to prevent publication.",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "location": {"type": "string"},
                },
                "required": ["category", "description", "location"],
                "additionalProperties": False,
            },
        },
        "issues": {
            "type": "array",
            "description": "All visible quality issues, including minor ones.",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["blocking", "major", "minor"],
                    },
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "location": {"type": "string"},
                },
                "required": ["severity", "category", "description", "location"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["score", "summary", "blocking_issues", "issues"],
    "additionalProperties": False,
}


class OllamaVisionError(Exception):
    """Raised when a local Ollama vision request cannot produce a valid report."""


def _image_to_base64(image_bytes: ImageBytes) -> str:
    if hasattr(image_bytes, "getvalue"):
        raw = image_bytes.getvalue()
    else:
        raw = bytes(image_bytes)

    if not raw:
        raise OllamaVisionError("Cannot evaluate an empty image payload.")

    return base64.b64encode(raw).decode("ascii")


def _images_to_base64(
    image_bytes: Union[ImageBytes, Sequence[ImageBytes]],
) -> List[str]:
    if isinstance(image_bytes, (bytes, bytearray, BytesIO)):
        images = [image_bytes]
    else:
        images = list(image_bytes)
    if not images:
        raise OllamaVisionError("At least one image view is required for visual QA.")
    return [_image_to_base64(image) for image in images]


def _extract_json_object(content: str) -> Dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise OllamaVisionError("Ollama returned a non-JSON visual QA response.")
        try:
            parsed = json.loads(text[start:end + 1])
        except json.JSONDecodeError as exc:
            raise OllamaVisionError(
                "Ollama returned malformed JSON for visual QA."
            ) from exc

    if not isinstance(parsed, dict):
        raise OllamaVisionError("Ollama visual QA response must be a JSON object.")
    return parsed


def _normalize_score(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise OllamaVisionError("Visual QA score must be an integer from 0 to 100.")
    if value < 0 or value > 100:
        raise OllamaVisionError("Visual QA score must be between 0 and 100.")
    return value


def _normalize_issue(issue: Any, default_severity: str) -> Dict[str, str]:
    if isinstance(issue, str):
        return {
            "severity": default_severity,
            "category": "other",
            "description": issue.strip() or "Unspecified issue",
            "location": "unspecified",
        }

    if not isinstance(issue, dict):
        return {
            "severity": default_severity,
            "category": "other",
            "description": str(issue),
            "location": "unspecified",
        }

    severity = str(issue.get("severity", default_severity)).strip().lower()
    if severity not in {"blocking", "major", "minor"}:
        severity = default_severity

    return {
        "severity": severity,
        "category": str(issue.get("category", "other")).strip() or "other",
        "description": (
            str(issue.get("description", "Unspecified issue")).strip()
            or "Unspecified issue"
        ),
        "location": (
            str(issue.get("location", "unspecified")).strip() or "unspecified"
        ),
    }


def _normalize_report(report: Dict[str, Any]) -> Dict[str, Any]:
    required = {"score", "summary", "blocking_issues", "issues"}
    missing = required.difference(report)
    if missing:
        raise OllamaVisionError(
            "Visual QA response is missing required fields: "
            + ", ".join(sorted(missing))
        )
    if not isinstance(report["summary"], str):
        raise OllamaVisionError("Visual QA summary must be a string.")
    if not isinstance(report["blocking_issues"], list):
        raise OllamaVisionError("Visual QA blocking_issues must be an array.")
    if not isinstance(report["issues"], list):
        raise OllamaVisionError("Visual QA issues must be an array.")

    issues_value = report["issues"]
    blocking_value = report["blocking_issues"]
    if any(not isinstance(issue, dict) for issue in blocking_value):
        raise OllamaVisionError("Each visual QA blocking issue must be an object.")
    if any(not isinstance(issue, dict) for issue in issues_value):
        raise OllamaVisionError("Each visual QA issue must be an object.")

    for issue in blocking_value:
        if not all(isinstance(issue.get(key), str) for key in (
            "category", "description", "location"
        )):
            raise OllamaVisionError(
                "Each blocking issue requires string category, description, and location."
            )
    for issue in issues_value:
        if issue.get("severity") not in {"blocking", "major", "minor"}:
            raise OllamaVisionError(
                "Each visual QA issue requires blocking, major, or minor severity."
            )
        if not all(isinstance(issue.get(key), str) for key in (
            "category", "description", "location"
        )):
            raise OllamaVisionError(
                "Each visual QA issue requires string category, description, and location."
            )

    issues = [
        _normalize_issue(issue, "major")
        for issue in issues_value if issue is not None
    ]
    explicit_blocking = [
        _normalize_issue(issue, "blocking")
        for issue in blocking_value if issue is not None
    ]

    blocking_issues: List[Dict[str, str]] = []
    seen = set()
    for issue in explicit_blocking + [
        issue for issue in issues if issue["severity"] == "blocking"
    ]:
        issue["severity"] = "blocking"
        key = (
            issue["category"],
            issue["description"],
            issue["location"],
        )
        if key not in seen:
            seen.add(key)
            blocking_issues.append(issue)

    model_score = _normalize_score(report["score"])
    if blocking_issues:
        score = 0
    else:
        major_count = sum(issue["severity"] == "major" for issue in issues)
        minor_count = sum(issue["severity"] == "minor" for issue in issues)
        score = max(0, 100 - (25 * major_count) - (5 * minor_count))

    return {
        "score": score,
        "model_score": model_score,
        "summary": report["summary"].strip(),
        "blocking_issues": blocking_issues,
        "issues": issues,
    }


def evaluate_image_with_ollama(
    image_bytes: Union[ImageBytes, Sequence[ImageBytes]],
    model: str,
    rubric: str,
    base_url: str = "http://localhost:11434",
    timeout: int = 300,
) -> Dict[str, Any]:
    """Evaluate one image through Ollama's structured multimodal chat API."""
    model = (model or "").strip()
    rubric = (rubric or "").strip()
    base_url = (base_url or "").strip().rstrip("/")

    if not model:
        raise OllamaVisionError("An Ollama vision model name is required.")
    if not rubric:
        raise OllamaVisionError("A visual QA rubric is required.")
    if not base_url.startswith(("http://", "https://")):
        raise OllamaVisionError("Ollama URL must start with http:// or https://.")

    system_prompt = (
        "You are a strict technical visual quality-control reviewer for "
        "AI-generated artwork. Inspect only what is visibly present and do not "
        "invent defects. Do not judge subject matter, mature content, artistic "
        "taste, or intentional stylization. Use blocking severity only for a "
        "severe technical image defect. Return only the requested JSON object."
    )
    user_prompt = (
        "Evaluate the attached views against the rubric below. The first image "
        "is the full frame; subsequent images are detail crops of the same "
        "artwork, ordered top-left, top-right, bottom-left, bottom-right. Do not "
        "report crop boundaries as defects. Use the crops to inspect faces, "
        "eyes, teeth, hands, fingers, limbs, edges, repeated patterns, text, "
        "and high-detail regions.\n\n"
        "Score is your diagnostic estimate only. Classify every observed defect "
        "with the correct severity; the client computes its gate score locally "
        "as 100 minus 25 per major issue and 5 per minor issue, with any "
        "blocking issue forcing zero.\n\n"
        f"Rubric:\n{rubric}"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt,
                "images": _images_to_base64(image_bytes),
            },
        ],
        "format": VISUAL_QA_SCHEMA,
        "stream": False,
        "think": False,
        # Ollama runs on a dedicated remote GPU. Keep the shared Qwen model warm
        # so the title and QA nodes do not reload it for every generated image.
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "seed": 0,
            "num_ctx": 16384,
            "num_predict": 1024,
        },
    }

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=(10, timeout),
        )
    except requests.exceptions.Timeout as exc:
        raise OllamaVisionError(
            f"Ollama visual QA timed out after {timeout} seconds."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise OllamaVisionError(
            f"Could not connect to Ollama at {base_url}."
        ) from exc
    except requests.RequestException as exc:
        raise OllamaVisionError(f"Ollama visual QA request failed: {exc}") from exc

    if response.status_code >= 400:
        try:
            error_body = response.json()
            detail = error_body.get("error") or error_body.get("message")
        except (ValueError, AttributeError):
            detail = None
        detail = str(detail or f"HTTP {response.status_code}")[:500]
        raise OllamaVisionError(f"Ollama visual QA failed: {detail}")

    try:
        response_data = response.json()
    except ValueError as exc:
        raise OllamaVisionError("Ollama returned an invalid HTTP JSON response.") from exc

    if not isinstance(response_data, dict):
        raise OllamaVisionError("Ollama HTTP response must be a JSON object.")

    message = response_data.get("message")
    if not isinstance(message, dict):
        raise OllamaVisionError("Ollama response is missing the assistant message.")

    content = message.get("content")
    thinking = message.get("thinking")
    if isinstance(content, str) and content.strip():
        structured_output = content
    elif isinstance(thinking, str) and thinking.strip():
        structured_output = thinking
    else:
        raise OllamaVisionError(
            "Ollama assistant message contains no visual QA JSON."
        )

    return _normalize_report(_extract_json_object(structured_output))
