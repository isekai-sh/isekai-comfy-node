import json
import unittest
from io import BytesIO
from unittest.mock import Mock, patch

import torch
from PIL import Image

from nodes.visual_qa_node import IsekaiVisualQA, _qa_image_views
from utils.ollama_vision_client import OllamaVisionError


def report(score=90, blocking_issues=None, issues=None):
    return {
        "score": score,
        "model_score": score,
        "summary": "Visual review result.",
        "blocking_issues": blocking_issues or [],
        "issues": issues or [],
    }


class IsekaiVisualQATests(unittest.TestCase):
    def setUp(self) -> None:
        self.image = torch.zeros((1, 4, 5, 3), dtype=torch.float32)
        self.pil_image = Image.new("RGB", (5, 4), "white")

    def evaluate(self, model_report, **kwargs):
        with patch("nodes.visual_qa_node.tensor_to_pil", return_value=self.pil_image), \
                patch("nodes.visual_qa_node.pil_to_bytes", return_value=BytesIO(b"png")), \
                patch(
                    "nodes.visual_qa_node.evaluate_image_with_ollama",
                    return_value=model_report,
                ) as evaluate_image, \
                patch("nodes.visual_qa_node._try_unload_comfy_models", return_value=[]):
            result = IsekaiVisualQA().evaluate(self.image, **kwargs)
        return result, evaluate_image

    def test_contract_and_defaults(self) -> None:
        inputs = IsekaiVisualQA.INPUT_TYPES()["required"]

        self.assertEqual(IsekaiVisualQA.RETURN_TYPES, ("IMAGE", "BOOLEAN", "INT", "STRING"))
        self.assertEqual(IsekaiVisualQA.RETURN_NAMES, ("image", "approved", "score", "report_json"))
        self.assertEqual(inputs["model"][1]["default"], "qwen3-vl:8b")
        self.assertEqual(inputs["approval_threshold"][1]["default"], 80)
        self.assertIs(inputs["unload_comfy_models"][1]["default"], True)

    def test_full_frame_and_quadrants_are_encoded_as_five_views(self) -> None:
        image = Image.new("RGB", (10, 8), "white")

        views = _qa_image_views(image)
        sizes = []
        for view in views:
            with Image.open(view) as encoded_image:
                sizes.append(encoded_image.size)

        self.assertEqual(sizes, [(10, 8), (5, 4), (5, 4), (5, 4), (5, 4)])

    def test_approves_at_threshold_with_no_blockers(self) -> None:
        result, evaluate_image = self.evaluate(
            report(score=80), approval_threshold=80, unload_comfy_models=False
        )
        output_image, approved, score, report_json = result
        parsed = json.loads(report_json)

        self.assertIs(output_image, self.image)
        self.assertIs(approved, True)
        self.assertEqual(score, 80)
        self.assertIs(parsed["approved"], True)
        self.assertEqual(parsed["batch_size"], 1)
        self.assertEqual(parsed["model_score"], 80)
        evaluate_image.assert_called_once()
        views = evaluate_image.call_args.kwargs["image_bytes"]
        self.assertEqual(len(views), 5)
        self.assertEqual([view.getvalue() for view in views], [b"png"] * 5)

    def test_rejects_high_score_when_any_blocking_issue_exists(self) -> None:
        blocker = {
            "severity": "blocking",
            "category": "anatomy",
            "description": "Fused fingers.",
            "location": "left hand",
        }
        result, _ = self.evaluate(report(score=100, blocking_issues=[blocker]))
        _, approved, score, report_json = result
        parsed = json.loads(report_json)

        self.assertIs(approved, False)
        self.assertEqual(score, 100)
        self.assertEqual(parsed["blocking_issues"][0]["batch_index"], 0)

    def test_batch_uses_lowest_score_and_aggregates_blockers(self) -> None:
        batch = torch.zeros((2, 4, 5, 3), dtype=torch.float32)
        blocker = {
            "severity": "blocking",
            "category": "artifact",
            "description": "Corrupt region.",
            "location": "right edge",
        }
        reports = [report(score=95), report(score=75, blocking_issues=[blocker])]
        with patch("nodes.visual_qa_node.tensor_to_pil", return_value=self.pil_image), \
                patch("nodes.visual_qa_node.pil_to_bytes", return_value=BytesIO(b"png")), \
                patch(
                    "nodes.visual_qa_node.evaluate_image_with_ollama",
                    side_effect=reports,
                ) as evaluate_image, \
                patch("nodes.visual_qa_node._try_unload_comfy_models", return_value=[]):
            output_image, approved, score, report_json = IsekaiVisualQA().evaluate(batch)
        parsed = json.loads(report_json)

        self.assertIs(output_image, batch)
        self.assertIs(approved, False)
        self.assertEqual(score, 75)
        self.assertEqual(parsed["batch_size"], 2)
        self.assertEqual(parsed["model_score"], 75)
        self.assertEqual(parsed["blocking_issues"][0]["batch_index"], 1)
        self.assertEqual(evaluate_image.call_count, 2)

    def test_inference_error_fails_closed(self) -> None:
        with patch("nodes.visual_qa_node.tensor_to_pil", return_value=self.pil_image), \
                patch("nodes.visual_qa_node.pil_to_bytes", return_value=BytesIO(b"png")), \
                patch(
                    "nodes.visual_qa_node.evaluate_image_with_ollama",
                    side_effect=OllamaVisionError("model unavailable"),
                ), patch("nodes.visual_qa_node._try_unload_comfy_models", return_value=[]):
            output_image, approved, score, report_json = IsekaiVisualQA().evaluate(self.image)
        parsed = json.loads(report_json)

        self.assertIs(output_image, self.image)
        self.assertIs(approved, False)
        self.assertEqual(score, 0)
        self.assertEqual(parsed["blocking_issues"][0]["category"], "inference_error")
        self.assertIn("model unavailable", parsed["blocking_issues"][0]["description"])

    def test_model_unload_failure_is_warning_not_gate_failure(self) -> None:
        with patch("nodes.visual_qa_node.tensor_to_pil", return_value=self.pil_image), \
                patch("nodes.visual_qa_node.pil_to_bytes", return_value=BytesIO(b"png")), \
                patch(
                    "nodes.visual_qa_node.evaluate_image_with_ollama",
                    return_value=report(score=90),
                ), patch(
                    "nodes.visual_qa_node._try_unload_comfy_models",
                    return_value=["Could not unload Comfy models: busy"],
                ):
            _, approved, _, report_json = IsekaiVisualQA().evaluate(self.image)
        parsed = json.loads(report_json)

        self.assertIs(approved, True)
        self.assertEqual(
            parsed["runtime_warnings"],
            ["Could not unload Comfy models: busy"],
        )


if __name__ == "__main__":
    unittest.main()
