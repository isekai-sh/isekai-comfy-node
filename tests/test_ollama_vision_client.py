import base64
import json
import unittest
from unittest.mock import Mock, patch

import requests

from utils.ollama_vision_client import (
    OllamaVisionError,
    VISUAL_QA_SCHEMA,
    evaluate_image_with_ollama,
)


class OllamaVisionClientTests(unittest.TestCase):
    @patch("utils.ollama_vision_client.requests.post")
    def test_sends_official_structured_vision_payload(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "message": {
                "content": json.dumps({
                    "score": 91,
                    "summary": "Ready with a small edge artifact.",
                    "blocking_issues": [],
                    "issues": [{
                        "severity": "minor",
                        "category": "artifact",
                        "description": "Small halo.",
                        "location": "lower edge",
                    }],
                })
            }
        }

        report = evaluate_image_with_ollama(
            b"PNG bytes",
            model="qwen3-vl:8b",
            rubric="Check anatomy and artifacts.",
            base_url="http://localhost:11434/",
        )

        self.assertEqual(report["score"], 95)
        self.assertEqual(report["model_score"], 91)
        self.assertEqual(report["blocking_issues"], [])
        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "http://localhost:11434/api/chat")
        payload = kwargs["json"]
        self.assertEqual(payload["model"], "qwen3-vl:8b")
        self.assertEqual(payload["format"], VISUAL_QA_SCHEMA)
        self.assertIs(payload["stream"], False)
        self.assertIs(payload["think"], False)
        self.assertEqual(payload["keep_alive"], "10m")
        self.assertEqual(payload["options"]["temperature"], 0)
        self.assertEqual(payload["options"]["seed"], 0)
        self.assertEqual(payload["options"]["num_ctx"], 16384)
        self.assertEqual(payload["options"]["num_predict"], 1024)
        self.assertEqual(len(payload["messages"][1]["images"]), 1)
        self.assertEqual(base64.b64decode(
            payload["messages"][1]["images"][0]
        ), b"PNG bytes")
        self.assertIn("Check anatomy and artifacts.", payload["messages"][1]["content"])
        self.assertEqual(kwargs["timeout"], (10, 300))

    @patch("utils.ollama_vision_client.requests.post")
    def test_blocking_issue_in_general_list_cannot_be_hidden(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "message": {
                "content": json.dumps({
                    "score": 100,
                    "summary": "Contradictory response.",
                    "blocking_issues": [],
                    "issues": [{
                        "severity": "blocking",
                        "category": "anatomy",
                        "description": "Primary hand is malformed.",
                        "location": "foreground hand",
                    }],
                })
            }
        }

        report = evaluate_image_with_ollama(
            b"image", "qwen3-vl:8b", "rubric"
        )

        self.assertEqual(report["score"], 0)
        self.assertEqual(report["model_score"], 100)
        self.assertEqual(len(report["blocking_issues"]), 1)
        self.assertEqual(report["blocking_issues"][0]["severity"], "blocking")

    @patch("utils.ollama_vision_client.requests.post")
    def test_sends_multiple_views_in_one_chat_request(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "message": {
                "content": json.dumps({
                    "score": 90,
                    "summary": "Technically clean.",
                    "blocking_issues": [],
                    "issues": [],
                })
            }
        }

        evaluate_image_with_ollama(
            [b"full", b"top-left", b"top-right", b"bottom-left", b"bottom-right"],
            "qwen3-vl:8b",
            "technical rubric",
        )

        encoded = post.call_args.kwargs["json"]["messages"][1]["images"]
        self.assertEqual(
            [base64.b64decode(image) for image in encoded],
            [b"full", b"top-left", b"top-right", b"bottom-left", b"bottom-right"],
        )
        self.assertEqual(post.call_count, 1)

    @patch("utils.ollama_vision_client.requests.post")
    def test_falls_back_to_qwen_thinking_when_content_is_empty(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "message": {
                "content": "",
                "thinking": json.dumps({
                    "score": 88,
                    "summary": "Technically clean.",
                    "blocking_issues": [],
                    "issues": [],
                }),
            }
        }

        result = evaluate_image_with_ollama(b"image", "model", "rubric")

        self.assertEqual(result["score"], 100)
        self.assertEqual(result["model_score"], 88)

    @patch("utils.ollama_vision_client.requests.post")
    def test_prefers_content_over_thinking(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "message": {
                "content": json.dumps({
                    "score": 92,
                    "summary": "Content result.",
                    "blocking_issues": [],
                    "issues": [],
                }),
                "thinking": json.dumps({
                    "score": 10,
                    "summary": "Thinking result.",
                    "blocking_issues": [],
                    "issues": [],
                }),
            }
        }

        result = evaluate_image_with_ollama(b"image", "model", "rubric")

        self.assertEqual(result["score"], 100)
        self.assertEqual(result["model_score"], 92)
        self.assertEqual(result["summary"], "Content result.")

    @patch("utils.ollama_vision_client.requests.post")
    def test_rejects_empty_content_and_thinking(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "message": {"content": "", "thinking": ""}
        }

        with self.assertRaisesRegex(OllamaVisionError, "contains no visual QA JSON"):
            evaluate_image_with_ollama(b"image", "model", "rubric")

    @patch("utils.ollama_vision_client.requests.post")
    def test_computes_gate_score_from_issue_severities(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "message": {
                "content": json.dumps({
                    "score": 1,
                    "summary": "One major and one minor defect.",
                    "blocking_issues": [],
                    "issues": [
                        {
                            "severity": "major",
                            "category": "anatomy",
                            "description": "Malformed hand.",
                            "location": "left hand",
                        },
                        {
                            "severity": "minor",
                            "category": "artifact",
                            "description": "Small halo.",
                            "location": "lower edge",
                        },
                    ],
                })
            }
        }

        result = evaluate_image_with_ollama(b"image", "model", "rubric")

        self.assertEqual(result["model_score"], 1)
        self.assertEqual(result["score"], 70)

    @patch("utils.ollama_vision_client.requests.post")
    def test_rejects_out_of_range_score_even_when_json_is_fenced(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "message": {
                "content": "```json\n"
                '{"score": 120, "summary": "ok", '
                '"blocking_issues": [], "issues": []}\n```'
            }
        }

        with self.assertRaisesRegex(OllamaVisionError, "between 0 and 100"):
            evaluate_image_with_ollama(b"image", "model", "rubric")

    @patch("utils.ollama_vision_client.requests.post")
    def test_rejects_invalid_structured_output(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "message": {"content": '{"summary": "missing score"}'}
        }

        with self.assertRaisesRegex(OllamaVisionError, "missing required fields"):
            evaluate_image_with_ollama(b"image", "model", "rubric")

    @patch("utils.ollama_vision_client.requests.post")
    def test_wraps_connection_errors(self, post: Mock) -> None:
        post.side_effect = requests.exceptions.ConnectionError("offline")

        with self.assertRaisesRegex(OllamaVisionError, "Could not connect"):
            evaluate_image_with_ollama(b"image", "model", "rubric")


if __name__ == "__main__":
    unittest.main()
