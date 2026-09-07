"""Compact, structured OpenRouter vision requests for Isekai Visual QA."""

import base64
import json
import os
from io import BytesIO
from typing import Any, Dict, List, Sequence, Union

import requests


DEFAULT_OPENROUTER_MODEL = "qwen/qwen3.8-flash"
DEFAULT_PRIMARY_FALLBACK_MODEL = "google/gemma-4-31b-it"
DEFAULT_SECONDARY_MODEL = "google/gemma-4-31b-it:free"
ImageBytes = Union[bytes, bytearray, BytesIO]

QA_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "pass": {"type": "boolean"},
        "reasons": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["pass", "reasons"],
    "additionalProperties": False,
}


class OpenRouterVisionError(Exception):
    """Raised when OpenRouter cannot produce a valid visual-QA decision."""


def _raw_image(image: ImageBytes) -> bytes:
    raw = image.getvalue() if hasattr(image, "getvalue") else bytes(image)
    if not raw:
        raise OpenRouterVisionError("Cannot evaluate an empty image payload.")
    return raw


def _image_content(images: Union[ImageBytes, Sequence[ImageBytes]]) -> List[Dict[str, Any]]:
    if isinstance(images, (bytes, bytearray, BytesIO)):
        image_list = [images]
    else:
        image_list = list(images)
    if not image_list:
        raise OpenRouterVisionError("At least one image view is required for visual QA.")

    return [
        {
            "type": "image_url",
            "image_url": {
                "url": "data:image/png;base64," + base64.b64encode(_raw_image(image)).decode("ascii")
            },
        }
        for image in image_list
    ]


def _extract_json_object(content: str) -> Dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines.pop()
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise OpenRouterVisionError("OpenRouter returned a non-JSON visual QA response.")
        try:
            parsed = json.loads(text[start:end + 1])
        except json.JSONDecodeError as exc:
            raise OpenRouterVisionError("OpenRouter returned malformed visual QA JSON.") from exc

    if not isinstance(parsed, dict):
        raise OpenRouterVisionError("OpenRouter visual QA response must be a JSON object.")
    return parsed


def _normalize_decision(value: Dict[str, Any]) -> Dict[str, Any]:
    passed = value.get("pass")
    reasons = value.get("reasons")
    if not isinstance(passed, bool):
        raise OpenRouterVisionError("Visual QA pass must be a boolean.")
    if not isinstance(reasons, list):
        raise OpenRouterVisionError("Visual QA reasons must be an array.")

    normalized_reasons = []
    for reason in reasons:
        if not isinstance(reason, dict) or not isinstance(reason.get("text"), str):
            raise OpenRouterVisionError("Every visual QA reason must contain text.")
        text = reason["text"].strip()
        if text:
            normalized_reasons.append({"text": text})

    if passed and normalized_reasons:
        raise OpenRouterVisionError("A passing visual QA decision cannot contain failure reasons.")
    if not passed and not normalized_reasons:
        raise OpenRouterVisionError("A failing visual QA decision must contain at least one reason.")
    return {"pass": passed, "reasons": normalized_reasons}


def _message_text(response_data: Dict[str, Any]) -> str:
    choices = response_data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenRouterVisionError("OpenRouter response contains no choices.")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise OpenRouterVisionError("OpenRouter response is missing the assistant message.")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        text = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and isinstance(part.get("text"), str)
        ).strip()
        if text:
            return text
    raise OpenRouterVisionError("OpenRouter assistant message contains no visual QA JSON.")


def _review(
    image_bytes: Union[ImageBytes, Sequence[ImageBytes]],
    model: str,
    rubric: str,
    generation_prompt: str,
    base_url: str,
    api_key: str,
    strict_schema: bool,
    timeout: int,
    fallback_models: Sequence[str] = (),
) -> Dict[str, Any]:
    system_prompt = (
        "You are a binary quality-control reviewer for generated character artwork. "
        "Return only the requested JSON. Pass only when the primary face is visible and "
        "readable, anatomy has no obvious failure, and the image is coherent with the final "
        "generation prompt. Ignore style preferences, tiny details, and harmless imperfections. "
        "Do not invent defects. Give short concrete reasons only when failing."
    )
    user_prompt = (
        "Review one artwork shown as a full frame followed by detail crops. All images are views "
        "of the same artwork; never treat crop boundaries as defects.\n\n"
        f"Final generation prompt:\n{generation_prompt or '(not supplied)'}\n\n"
        f"Additional rubric:\n{rubric}"
    )
    response_format: Dict[str, Any]
    if strict_schema:
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": "isekai_visual_qa", "strict": True, "schema": QA_SCHEMA},
        }
    else:
        response_format = {"type": "json_object"}

    models = list(dict.fromkeys([model, *[value for value in fallback_models if value]]))
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [{"type": "text", "text": user_prompt}] + _image_content(image_bytes),
            },
        ],
        "response_format": response_format,
        "reasoning": {"effort": "none"},
        "temperature": 0,
        "max_tokens": 192,
        "stream": False,
    }
    if len(models) > 1:
        payload["models"] = models
    else:
        payload["model"] = model
    if strict_schema:
        payload["provider"] = {"require_parameters": True}

    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://isekai.sh",
                "X-Title": "Isekai Visual QA",
            },
            json=payload,
            timeout=(10, timeout),
        )
    except requests.exceptions.Timeout as exc:
        raise OpenRouterVisionError(f"OpenRouter visual QA timed out after {timeout} seconds.") from exc
    except requests.exceptions.ConnectionError as exc:
        raise OpenRouterVisionError("Could not connect to OpenRouter.") from exc
    except requests.RequestException as exc:
        raise OpenRouterVisionError(f"OpenRouter visual QA request failed: {exc}") from exc

    if response.status_code >= 400:
        try:
            body = response.json()
            error = body.get("error") if isinstance(body, dict) else None
            if isinstance(error, dict):
                metadata = error.get("metadata")
                detail = metadata.get("raw") if isinstance(metadata, dict) else None
                detail = detail or error.get("message")
            else:
                detail = error
        except (ValueError, AttributeError):
            detail = None
        detail = str(detail or f"HTTP {response.status_code}")[:500]
        raise OpenRouterVisionError(f"OpenRouter visual QA failed: {detail}")

    try:
        response_data = response.json()
    except ValueError as exc:
        raise OpenRouterVisionError("OpenRouter returned an invalid HTTP JSON response.") from exc
    if not isinstance(response_data, dict):
        raise OpenRouterVisionError("OpenRouter HTTP response must be a JSON object.")

    decision = _normalize_decision(_extract_json_object(_message_text(response_data)))
    resolved_model = response_data.get("model")
    if isinstance(resolved_model, str) and resolved_model.strip():
        decision["resolved_model"] = resolved_model.strip()
    usage = response_data.get("usage")
    if isinstance(usage, dict):
        decision["usage"] = {
            key: usage[key]
            for key in ("prompt_tokens", "completion_tokens", "total_tokens", "cost")
            if isinstance(usage.get(key), (int, float)) and not isinstance(usage.get(key), bool)
        }
    return decision


def evaluate_image_with_openrouter(
    image_bytes: Union[ImageBytes, Sequence[ImageBytes]],
    model: str = DEFAULT_OPENROUTER_MODEL,
    rubric: str = "",
    generation_prompt: str = "",
    base_url: str = "https://openrouter.ai/api/v1",
    secondary_model: str = DEFAULT_SECONDARY_MODEL,
    timeout: int = 180,
) -> Dict[str, Any]:
    """Run paid primary QA plus an optional free-model agreement gate."""
    model = (model or "").strip()
    secondary_model = (secondary_model or "").strip()
    rubric = (rubric or "").strip()
    base_url = (base_url or "").strip().rstrip("/")
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not model:
        raise OpenRouterVisionError("An OpenRouter vision model name is required.")
    if not rubric:
        raise OpenRouterVisionError("A visual QA rubric is required.")
    if not base_url.startswith(("http://", "https://")):
        raise OpenRouterVisionError("OpenRouter URL must start with http:// or https://.")
    if not api_key:
        raise OpenRouterVisionError("OPENROUTER_API_KEY is not configured for ComfyUI.")

    primary = _review(
        image_bytes,
        model,
        rubric,
        generation_prompt,
        base_url,
        api_key,
        True,
        timeout,
        (DEFAULT_PRIMARY_FALLBACK_MODEL,),
    )
    secondary = None
    warnings: List[str] = []
    if secondary_model and secondary_model != model:
        try:
            secondary = _review(
                image_bytes,
                secondary_model,
                rubric,
                generation_prompt,
                base_url,
                api_key,
                False,
                timeout,
            )
        except OpenRouterVisionError as exc:
            warnings.append(f"Secondary reviewer unavailable: {exc}")

    approved = primary["pass"] and (secondary is None or secondary["pass"])
    reviews = [("primary", primary)]
    if secondary is not None:
        reviews.append(("secondary", secondary))
    reasons = [
        {"reviewer": reviewer, "text": reason["text"]}
        for reviewer, decision in reviews
        if not decision["pass"]
        for reason in decision["reasons"]
    ]
    blocking_issues = [
        {
            "severity": "blocking",
            "category": "visual_qa",
            "description": reason["text"],
            "location": "image",
            "reviewer": reason["reviewer"],
        }
        for reason in reasons
    ]
    return {
        "score": 100 if approved else 0,
        "model_score": 100 if primary["pass"] else 0,
        "summary": "Passed visual QA." if approved else "; ".join(r["text"] for r in reasons),
        "blocking_issues": blocking_issues,
        "issues": blocking_issues,
        "provider": "openrouter",
        "primary": {"model": model, **primary},
        "secondary": ({"model": secondary_model, **secondary} if secondary is not None else None),
        "runtime_warnings": warnings,
    }
