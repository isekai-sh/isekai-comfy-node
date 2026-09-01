import unittest
from unittest.mock import patch

from nodes.ollama_summarizer_node import IsekaiOllamaSummarizer
from utils.ollama_client import (
    OLLAMA_RESPONSE_MODE_GENERAL,
    OLLAMA_RESPONSE_MODE_SHORT,
)


class IsekaiOllamaSummarizerTests(unittest.TestCase):
    def test_model_is_free_text_for_remote_ollama_servers(self) -> None:
        model_input = IsekaiOllamaSummarizer.INPUT_TYPES()["required"]["model"]

        self.assertEqual(model_input[0], "STRING")
        self.assertEqual(model_input[1]["default"], "qwen3-vl:8b")

    def test_response_mode_is_appended_and_defaults_to_general(self) -> None:
        optional = IsekaiOllamaSummarizer.INPUT_TYPES()["optional"]

        self.assertEqual(
            list(optional),
            ["system_prompt", "ollama_url", "response_mode"],
        )
        response_mode = optional["response_mode"]
        self.assertEqual(
            response_mode[0],
            [OLLAMA_RESPONSE_MODE_GENERAL, OLLAMA_RESPONSE_MODE_SHORT],
        )
        self.assertEqual(
            response_mode[1]["default"],
            OLLAMA_RESPONSE_MODE_GENERAL,
        )

    @patch("nodes.ollama_summarizer_node.generate_text")
    def test_forwards_remote_url_and_model(self, generate_text) -> None:
        generate_text.return_value = {
            "success": True,
            "text": "Generated title",
            "error": None,
        }

        result = IsekaiOllamaSummarizer().generate(
            prompt="portrait prompt",
            model="qwen3-vl:8b",
            system_prompt="Create a title",
            ollama_url="http://ollama.example.test:11434",
        )

        self.assertEqual(result, ("Generated title",))
        generate_text.assert_called_once_with(
            text="portrait prompt",
            model="qwen3-vl:8b",
            base_url="http://ollama.example.test:11434",
            system_prompt="Create a title",
            response_mode=OLLAMA_RESPONSE_MODE_GENERAL,
        )

    @patch("nodes.ollama_summarizer_node.generate_text")
    def test_forwards_short_response_mode(self, generate_text) -> None:
        generate_text.return_value = {
            "success": True,
            "text": "Generated title",
            "error": None,
        }

        IsekaiOllamaSummarizer().generate(
            prompt="portrait prompt",
            model="qwen3-vl:8b",
            response_mode=OLLAMA_RESPONSE_MODE_SHORT,
        )

        self.assertEqual(
            generate_text.call_args.kwargs["response_mode"],
            OLLAMA_RESPONSE_MODE_SHORT,
        )


if __name__ == "__main__":
    unittest.main()
