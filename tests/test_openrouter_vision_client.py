import base64
import json
import os
import unittest
from unittest.mock import Mock, patch

import requests

from utils.openrouter_vision_client import (
    OpenRouterVisionError,
    QA_SCHEMA,
    evaluate_image_with_openrouter,
)


def response(decision, usage=None):
    result = {
        "choices": [{"message": {"content": json.dumps(decision)}}],
    }
    if usage is not None:
        result["usage"] = usage
    mock = Mock(status_code=200)
    mock.json.return_value = result
    return mock


class OpenRouterVisionClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.key = patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"})
        self.key.start()

    def tearDown(self) -> None:
        self.key.stop()

    @patch("utils.openrouter_vision_client.requests.post")
    def test_primary_and_free_secondary_must_both_pass(self, post: Mock) -> None:
        post.side_effect = [
            response({"pass": True, "reasons": []}, {"prompt_tokens": 10, "completion_tokens": 4}),
            response({"pass": False, "reasons": [{"text": "The left arm is duplicated."}]}),
        ]

        report = evaluate_image_with_openrouter(
            [b"full", b"detail"],
            generation_prompt="one woman holding a sword",
            rubric="Check face, anatomy, and prompt coherence.",
        )

        self.assertEqual(post.call_count, 2)
        self.assertEqual(report["score"], 0)
        self.assertEqual(report["model_score"], 100)
        self.assertFalse(report["secondary"]["pass"])
        self.assertEqual(report["blocking_issues"][0]["reviewer"], "secondary")

        primary_payload = post.call_args_list[0].kwargs["json"]
        self.assertEqual(primary_payload["model"], "qwen/qwen3.8-flash")
        self.assertEqual(
            primary_payload["response_format"]["json_schema"]["schema"],
            QA_SCHEMA,
        )
        self.assertEqual(primary_payload["reasoning"], {"effort": "none"})
        self.assertEqual(primary_payload["max_tokens"], 192)
        self.assertTrue(primary_payload["provider"]["require_parameters"])
        content = primary_payload["messages"][1]["content"]
        self.assertIn("one woman holding a sword", content[0]["text"])
        encoded = [part["image_url"]["url"].split(",", 1)[1] for part in content[1:]]
        self.assertEqual([base64.b64decode(value) for value in encoded], [b"full", b"detail"])

        secondary_payload = post.call_args_list[1].kwargs["json"]
        self.assertEqual(secondary_payload["model"], "google/gemma-4-31b-it:free")
        self.assertEqual(secondary_payload["response_format"], {"type": "json_object"})
        self.assertNotIn("provider", secondary_payload)

    @patch("utils.openrouter_vision_client.requests.post")
    def test_secondary_outage_does_not_override_primary(self, post: Mock) -> None:
        unavailable = Mock(status_code=429)
        unavailable.json.return_value = {"error": {"message": "free-model rate limit"}}
        post.side_effect = [response({"pass": True, "reasons": []}), unavailable]

        report = evaluate_image_with_openrouter(b"image", rubric="rubric")

        self.assertEqual(report["score"], 100)
        self.assertIsNone(report["secondary"])
        self.assertIn("Secondary reviewer unavailable", report["runtime_warnings"][0])

    @patch("utils.openrouter_vision_client.requests.post")
    def test_primary_failure_is_not_hidden(self, post: Mock) -> None:
        post.return_value = response({"pass": False, "reasons": [{"text": "No visible face."}]})

        report = evaluate_image_with_openrouter(
            b"image", rubric="rubric", secondary_model=""
        )

        self.assertEqual(report["score"], 0)
        self.assertEqual(report["blocking_issues"][0]["description"], "No visible face.")
        self.assertIsNone(report["secondary"])

    @patch("utils.openrouter_vision_client.requests.post")
    def test_rejects_inconsistent_compact_json(self, post: Mock) -> None:
        post.return_value = response({"pass": True, "reasons": [{"text": "bad hand"}]})

        with self.assertRaisesRegex(OpenRouterVisionError, "passing.*cannot contain"):
            evaluate_image_with_openrouter(b"image", rubric="rubric", secondary_model="")

    @patch("utils.openrouter_vision_client.requests.post")
    def test_wraps_connection_error(self, post: Mock) -> None:
        post.side_effect = requests.exceptions.ConnectionError("offline")

        with self.assertRaisesRegex(OpenRouterVisionError, "Could not connect"):
            evaluate_image_with_openrouter(b"image", rubric="rubric", secondary_model="")

    def test_requires_environment_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(OpenRouterVisionError, "OPENROUTER_API_KEY"):
                evaluate_image_with_openrouter(b"image", rubric="rubric")


if __name__ == "__main__":
    unittest.main()
