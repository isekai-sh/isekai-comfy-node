import unittest
from unittest.mock import Mock, patch

from utils.ollama_client import (
    OLLAMA_RESPONSE_MODE_SHORT,
    generate_text,
)


class OllamaClientTests(unittest.TestCase):
    @patch("utils.ollama_client.requests.post")
    def test_short_generation_disables_thinking_and_keeps_model_warm(
        self, post: Mock
    ) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "response": "",
            "thinking": '{"response": "Short Title"}',
        }

        result = generate_text(
            "source prompt",
            "qwen3-vl:8b",
            base_url="http://ollama.example.test:11434/",
            system_prompt="Write a title.",
            response_mode=OLLAMA_RESPONSE_MODE_SHORT,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "Short Title")
        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args[0], "http://ollama.example.test:11434/api/generate")
        payload = kwargs["json"]
        self.assertEqual(payload["format"]["required"], ["response"])
        self.assertIs(payload["think"], False)
        self.assertEqual(payload["keep_alive"], "10m")
        self.assertEqual(payload["options"]["temperature"], 0)
        self.assertEqual(payload["options"]["seed"], 0)
        self.assertEqual(payload["options"]["num_ctx"], 16384)
        self.assertEqual(payload["options"]["num_predict"], 64)
        self.assertEqual(payload["prompt"], "Write a title.\n\nsource prompt")

    @patch("utils.ollama_client.requests.post")
    def test_accepts_structured_output_from_response_field(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "response": '{"response": "Structured Title"}'
        }

        result = generate_text(
            "prompt",
            "model",
            response_mode=OLLAMA_RESPONSE_MODE_SHORT,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "Structured Title")

    @patch("utils.ollama_client.requests.post")
    def test_general_generation_uses_plain_untuned_payload(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "response": "A normal general-purpose answer"
        }

        result = generate_text(
            "prompt",
            "model",
            base_url="http://ollama.example.test:11434",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "A normal general-purpose answer")
        self.assertEqual(
            post.call_args.kwargs["json"],
            {
                "model": "model",
                "prompt": "prompt",
                "stream": False,
            },
        )

    @patch("utils.ollama_client.requests.post")
    def test_general_generation_does_not_read_thinking_fallback(self, post: Mock) -> None:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "response": "",
            "thinking": "Hidden chain of thought",
        }

        result = generate_text("prompt", "model")

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Ollama returned empty response")


if __name__ == "__main__":
    unittest.main()
