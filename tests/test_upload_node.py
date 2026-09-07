import json
import unittest
from io import BytesIO
from inspect import signature
from unittest.mock import Mock, patch

from nodes.upload_node import (
    IsekaiUploadNode,
    QA_UNAVAILABLE_REASON,
    SUBMISSION_POLICY_DIRECT_TO_DRAFT,
    SUBMISSION_POLICY_MANUAL_REVIEW,
    SUBMISSION_POLICY_USE_QA_DECISION,
)


class IsekaiUploadSubmissionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.node = IsekaiUploadNode()

    def test_submission_policy_widget_is_appended_and_defaults_to_manual(self):
        optional_inputs = IsekaiUploadNode.INPUT_TYPES()["optional"]

        self.assertEqual(
            list(optional_inputs),
            [
                "api_key",
                "api_url",
                "tags",
                "format",
                "quality",
                "submission_policy",
                "qa_approved",
                "generation_run_id",
                "generation_output_key",
                "qa_report",
            ],
        )
        options, config = optional_inputs["submission_policy"]
        self.assertEqual(
            options,
            [
                SUBMISSION_POLICY_MANUAL_REVIEW,
                SUBMISSION_POLICY_DIRECT_TO_DRAFT,
                SUBMISSION_POLICY_USE_QA_DECISION,
            ],
        )
        self.assertEqual(config["default"], SUBMISSION_POLICY_MANUAL_REVIEW)
        qa_type, qa_config = optional_inputs["qa_approved"]
        self.assertEqual(qa_type, "BOOLEAN")
        self.assertFalse(qa_config["default"])
        self.assertTrue(qa_config["forceInput"])
        self.assertEqual(
            signature(IsekaiUploadNode.upload)
            .parameters["submission_policy"]
            .default,
            SUBMISSION_POLICY_MANUAL_REVIEW,
        )
        self.assertFalse(
            signature(IsekaiUploadNode.upload)
            .parameters["qa_approved"]
            .default
        )
        self.assertEqual(
            list(signature(IsekaiUploadNode.upload).parameters)[-1],
            "qa_report",
        )

    def test_qa_report_is_reduced_to_bounded_review_context(self):
        report = json.dumps(
            {
                "approved": False,
                "score": 0,
                "final_prompt": "must never be forwarded",
                "blocking_issues": [
                    {
                        "category": "anatomy",
                        "description": "The left hand has duplicated fingers.",
                        "location": "left hand",
                    }
                ],
            }
        )

        summary = json.loads(self.node._summarize_qa_report(report, False))

        self.assertEqual(
            summary,
            {
                "source": "visual_qa",
                "approved": False,
                "score": 0,
                "reasons": [
                    {
                        "text": "The left hand has duplicated fingers.",
                        "category": "anatomy",
                        "location": "left hand",
                    }
                ],
            },
        )
        self.assertNotIn("final_prompt", summary)

    def test_inference_failure_is_not_exposed_as_a_review_reason(self):
        internal_error = "OpenRouter visual QA response must be a JSON object."
        report = json.dumps(
            {
                "approved": False,
                "score": 0,
                "blocking_issues": [
                    {
                        "category": "inference_error",
                        "description": internal_error,
                        "location": "visual_qa",
                    }
                ],
            }
        )

        summary = json.loads(self.node._summarize_qa_report(report, False))

        self.assertEqual(
            summary["reasons"],
            [{"text": QA_UNAVAILABLE_REASON, "category": "qa_unavailable"}],
        )
        self.assertNotIn(internal_error, json.dumps(summary))

    def test_policy_labels_map_to_wire_values(self):
        self.assertEqual(
            self.node._get_review_policy(SUBMISSION_POLICY_MANUAL_REVIEW),
            "manual_review",
        )
        self.assertEqual(
            self.node._get_review_policy(SUBMISSION_POLICY_DIRECT_TO_DRAFT),
            "direct_to_draft",
        )

    def test_qa_policy_uses_boolean_approval_and_fails_closed(self):
        self.assertEqual(
            self.node._get_review_policy(SUBMISSION_POLICY_USE_QA_DECISION, True),
            "direct_to_draft",
        )
        self.assertEqual(
            self.node._get_review_policy(SUBMISSION_POLICY_USE_QA_DECISION, False),
            "manual_review",
        )
        self.assertEqual(
            self.node._get_review_policy(SUBMISSION_POLICY_USE_QA_DECISION),
            "manual_review",
        )
        self.assertEqual(
            self.node._get_review_policy(SUBMISSION_POLICY_USE_QA_DECISION, "true"),
            "manual_review",
        )

    def test_missing_or_unknown_policy_fails_closed_to_manual_review(self):
        self.assertEqual(self.node._get_review_policy(), "manual_review")
        self.assertEqual(self.node._get_review_policy(None), "manual_review")
        self.assertEqual(self.node._get_review_policy("unexpected"), "manual_review")

    @patch("nodes.upload_node.pil_to_bytes", return_value=BytesIO(b"image"))
    @patch("nodes.upload_node.tensor_to_pil", return_value=Mock())
    @patch("nodes.upload_node.validate_title", return_value=(True, "Test", ""))
    @patch("nodes.upload_node.validate_api_key", return_value=(True, ""))
    def test_upload_maps_direct_to_draft_before_request(
        self,
        _validate_api_key: Mock,
        _validate_title: Mock,
        _tensor_to_pil: Mock,
        _pil_to_bytes: Mock,
    ):
        self.node._get_api_key = Mock(return_value="test-key")
        self.node._get_api_url = Mock(return_value="https://isekai.example")
        self.node._generate_filename = Mock(return_value="test.png")
        self.node._upload_to_isekai = Mock(
            return_value={"status": "queued", "deviationId": "test"}
        )
        image = Mock()

        result = self.node.upload(
            image=image,
            title="Test",
            submission_policy=SUBMISSION_POLICY_DIRECT_TO_DRAFT,
        )

        metadata = self.node._upload_to_isekai.call_args.args[4]
        self.assertEqual(metadata["reviewPolicy"], "direct_to_draft")
        self.assertIs(result[0], image)

    @patch("nodes.upload_node.pil_to_bytes", return_value=BytesIO(b"image"))
    @patch("nodes.upload_node.tensor_to_pil", return_value=Mock())
    @patch("nodes.upload_node.validate_title", return_value=(True, "Test", ""))
    @patch("nodes.upload_node.validate_api_key", return_value=(True, ""))
    def test_upload_accepts_generation_correlation_inputs(
        self,
        _validate_api_key: Mock,
        _validate_title: Mock,
        _tensor_to_pil: Mock,
        _pil_to_bytes: Mock,
    ):
        self.node._get_api_key = Mock(return_value="test-key")
        self.node._get_api_url = Mock(return_value="https://isekai.example")
        self.node._generate_filename = Mock(return_value="test.png")
        self.node._upload_to_isekai = Mock(
            return_value={"status": "queued", "deviationId": "test"}
        )

        self.node.upload(
            image=Mock(),
            title="Test",
            generation_run_id="run-1",
            generation_output_key="run-1:0",
        )

        metadata = self.node._upload_to_isekai.call_args.args[4]
        self.assertEqual(metadata["generationRunId"], "run-1")
        self.assertEqual(metadata["generationOutputKey"], "run-1:0")

    @patch("nodes.upload_node.pil_to_bytes", return_value=BytesIO(b"image"))
    @patch("nodes.upload_node.tensor_to_pil", return_value=Mock())
    @patch("nodes.upload_node.validate_title", return_value=(True, "Test", ""))
    @patch("nodes.upload_node.validate_api_key", return_value=(True, ""))
    def test_upload_uses_qa_decision_before_request(
        self,
        _validate_api_key: Mock,
        _validate_title: Mock,
        _tensor_to_pil: Mock,
        _pil_to_bytes: Mock,
    ):
        self.node._get_api_key = Mock(return_value="test-key")
        self.node._get_api_url = Mock(return_value="https://isekai.example")
        self.node._generate_filename = Mock(return_value="test.png")
        self.node._upload_to_isekai = Mock(
            return_value={"status": "queued", "deviationId": "test"}
        )
        image = Mock()

        self.node.upload(
            image=image,
            title="Test",
            submission_policy=SUBMISSION_POLICY_USE_QA_DECISION,
            qa_approved=True,
        )
        approved_metadata = self.node._upload_to_isekai.call_args.args[4]
        self.assertEqual(approved_metadata["reviewPolicy"], "direct_to_draft")

        self.node.upload(
            image=image,
            title="Test",
            submission_policy=SUBMISSION_POLICY_USE_QA_DECISION,
        )
        unapproved_metadata = self.node._upload_to_isekai.call_args.args[4]
        self.assertEqual(unapproved_metadata["reviewPolicy"], "manual_review")

    @patch("nodes.upload_node.requests.post")
    def test_multipart_request_includes_review_policy(self, post: Mock):
        response = Mock(status_code=200)
        response.json.return_value = {"status": "queued"}
        post.return_value = response

        self.node._upload_to_isekai(
            image_bytes=b"image",
            filename="test.png",
            api_key="test-key",
            api_url="https://isekai.example",
            metadata={
                "title": "Test",
                "tags": "",
                "reviewPolicy": "direct_to_draft",
            },
            format="PNG",
        )

        self.assertEqual(
            post.call_args.kwargs["data"]["reviewPolicy"],
            "direct_to_draft",
        )

    @patch("nodes.upload_node.requests.post")
    def test_multipart_request_includes_generation_correlation(self, post: Mock):
        response = Mock(status_code=200)
        response.json.return_value = {"status": "draft"}
        post.return_value = response

        self.node._upload_to_isekai(
            image_bytes=b"image",
            filename="test.png",
            api_key="test-key",
            api_url="https://isekai.example",
            metadata={
                "title": "Test",
                "tags": "",
                "reviewPolicy": "direct_to_draft",
                "generationRunId": "run-1",
                "generationOutputKey": "run-1:0",
            },
            format="PNG",
        )

        self.assertEqual(post.call_args.kwargs["data"]["generationRunId"], "run-1")
        self.assertEqual(
            post.call_args.kwargs["data"]["generationOutputKey"],
            "run-1:0",
        )

    @patch("nodes.upload_node.requests.post")
    def test_multipart_request_includes_generation_qa(self, post: Mock):
        response = Mock(status_code=200)
        response.json.return_value = {"status": "review"}
        post.return_value = response
        qa_summary = '{"source":"visual_qa","approved":false,"score":0,"reasons":[]}'

        self.node._upload_to_isekai(
            image_bytes=b"image",
            filename="test.png",
            api_key="test-key",
            api_url="https://isekai.example",
            metadata={
                "title": "Test",
                "tags": "",
                "reviewPolicy": "manual_review",
                "generationQa": qa_summary,
            },
            format="PNG",
        )

        self.assertEqual(post.call_args.kwargs["data"]["generationQa"], qa_summary)

    @patch("nodes.upload_node.requests.post")
    def test_internal_upload_call_defaults_to_manual_review(self, post: Mock):
        response = Mock(status_code=200)
        response.json.return_value = {"status": "queued"}
        post.return_value = response

        self.node._upload_to_isekai(
            image_bytes=b"image",
            filename="test.png",
            api_key="test-key",
            api_url="https://isekai.example",
            metadata={"title": "Test", "tags": ""},
            format="PNG",
        )

        self.assertEqual(
            post.call_args.kwargs["data"]["reviewPolicy"],
            "manual_review",
        )


if __name__ == "__main__":
    unittest.main()
