"""
Unit tests for UserImageAnalyzer and generate_workout_prompt.
All external calls (genai, filesystem) are mocked.
"""
import io
import json
import os
from unittest.mock import Mock, patch, MagicMock

import pytest

from backend.analyzers.user_image_analyzer import (
    UserImageAnalyzer,
    generate_workout_prompt,
    BODYTYPE_JSON_PROMPT,
)

PATCH_GENAI = "backend.analyzers.user_image_analyzer.genai"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BODY_ANALYSIS_JSON = json.dumps({
    "body_type": "mesomorph",
    "primary_focus": "chest",
    "secondary_focuses": ["back", "shoulders"],
    "rationale": "Athletic build",
})

WORKOUT_PLAN_JSON = json.dumps({
    "days": [
        {
            "day": 1,
            "focus": "chest",
            "exercises": [
                {
                    "name": "Bench Press",
                    "muscle_group": "chest",
                    "reps": "8-12",
                    "sets": 3,
                    "rest_seconds": 90,
                    "form_tips": "Keep back flat",
                }
            ],
        }
    ],
    "days_per_week": 1,
    "notes": "Good luck",
})


def _mock_genai_responses(body_text=BODY_ANALYSIS_JSON, workout_text=WORKOUT_PLAN_JSON):
    body_resp = Mock()
    body_resp.text = body_text
    workout_resp = Mock()
    workout_resp.text = workout_text
    return body_resp, workout_resp


def _make_analyzer(image_bytes=None, image_path=None, **kwargs):
    if image_bytes is None and image_path is None:
        image_bytes = io.BytesIO(b"\xff\xd8\xff" * 10)
    return UserImageAnalyzer(
        image_bytes=image_bytes,
        image_path=image_path,
        api_key="fake-key",
        **kwargs,
    )


# ---------------------------------------------------------------------------
# generate_workout_prompt
# ---------------------------------------------------------------------------

class TestGenerateWorkoutPrompt:
    def test_returns_string(self):
        prompt = generate_workout_prompt("mesomorph", "chest", ["back", "shoulders"])
        assert isinstance(prompt, str)
        assert "mesomorph" in prompt
        assert "chest" in prompt

    def test_beginner_rep_range(self):
        prompt = generate_workout_prompt("ectomorph", "legs", [], difficulty="beginner")
        assert "10-15 reps" in prompt

    def test_advanced_rep_range(self):
        prompt = generate_workout_prompt("endomorph", "back", [], difficulty="advanced")
        assert "3-8 reps" in prompt

    def test_intermediate_rep_range(self):
        prompt = generate_workout_prompt("mesomorph", "chest", [], difficulty="intermediate")
        assert "6-12 reps" in prompt

    def test_days_per_week_included_in_prompt(self):
        prompt = generate_workout_prompt("mesomorph", "chest", ["back"], days_per_week=6)
        assert "6" in prompt

    def test_empty_secondary_focuses(self):
        prompt = generate_workout_prompt("ectomorph", "shoulders", [])
        assert "shoulders" in prompt

    def test_many_days_per_week(self):
        prompt = generate_workout_prompt("endomorph", "legs", ["core"], days_per_week=7)
        assert "7" in prompt
        assert "Day 7" in prompt


# ---------------------------------------------------------------------------
# UserImageAnalyzer.analyze — image_bytes path
# ---------------------------------------------------------------------------

class TestUserImageAnalyzerFromBytes:
    def test_analyze_success_from_bytes(self):
        body_resp, workout_resp = _mock_genai_responses()
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = [body_resp, workout_resp]

        analyzer = _make_analyzer()

        with patch(PATCH_GENAI) as mock_genai:
            mock_genai.Client.return_value = mock_client
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            result = analyzer.analyze()

        assert result["type"] == "user_image"
        assert result["result"]["body_type"] == "mesomorph"
        assert result["result"]["workout_plan"]["days_per_week"] == 1

    def test_analyze_sets_api_key_from_env(self):
        body_resp, workout_resp = _mock_genai_responses()
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = [body_resp, workout_resp]

        analyzer = UserImageAnalyzer(
            image_bytes=io.BytesIO(b"\x00" * 10),
            api_key=None,
        )

        with patch.dict(os.environ, {"GEMINI_API_KEY": "env-key"}), \
             patch(PATCH_GENAI) as mock_genai:
            mock_genai.Client.return_value = mock_client
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            result = analyzer.analyze()

        assert result["type"] == "user_image"

    def test_analyze_raises_when_no_api_key(self):
        analyzer = UserImageAnalyzer(image_bytes=io.BytesIO(b"\x00" * 10), api_key=None)

        saved = os.environ.pop("GEMINI_API_KEY", None)
        try:
            with patch(PATCH_GENAI):
                with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                    analyzer.analyze()
        finally:
            if saved is not None:
                os.environ["GEMINI_API_KEY"] = saved

    def test_analyze_raises_when_no_source(self):
        analyzer = UserImageAnalyzer(api_key="key")

        with patch(PATCH_GENAI):
            with pytest.raises(ValueError, match="Must provide"):
                analyzer.analyze()

    def test_analyze_workout_json_decode_error_uses_fallback(self):
        """When Gemini returns invalid JSON for the workout plan, fallback is used."""
        body_resp = Mock()
        body_resp.text = BODY_ANALYSIS_JSON
        bad_workout_resp = Mock()
        bad_workout_resp.text = "not json at all"

        mock_client = Mock()
        mock_client.models.generate_content.side_effect = [body_resp, bad_workout_resp]

        analyzer = _make_analyzer()

        with patch(PATCH_GENAI) as mock_genai:
            mock_genai.Client.return_value = mock_client
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            result = analyzer.analyze()

        # Should still return a result using the fallback
        assert result["result"]["workout_plan"]["days"] == []
        assert "Error generating plan" in result["result"]["workout_plan"]["notes"]

    def test_analyze_body_json_decode_error_raises(self):
        """When body analysis JSON is invalid, ValueError is raised."""
        bad_body_resp = Mock()
        bad_body_resp.text = "INVALID JSON"

        mock_client = Mock()
        mock_client.models.generate_content.return_value = bad_body_resp

        analyzer = _make_analyzer()

        with patch(PATCH_GENAI) as mock_genai:
            mock_genai.Client.return_value = mock_client
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            with pytest.raises(ValueError, match="non-JSON"):
                analyzer.analyze()


# ---------------------------------------------------------------------------
# UserImageAnalyzer.analyze — image_path path
# ---------------------------------------------------------------------------

class TestUserImageAnalyzerFromPath:
    def test_analyze_success_from_path(self, tmp_path):
        img_file = tmp_path / "test.jpg"
        img_file.write_bytes(b"\xff\xd8\xff" * 100)

        body_resp, workout_resp = _mock_genai_responses()
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = [body_resp, workout_resp]

        analyzer = UserImageAnalyzer(image_path=str(img_file), api_key="key")

        with patch(PATCH_GENAI) as mock_genai:
            mock_genai.Client.return_value = mock_client
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            result = analyzer.analyze()

        assert result["input_source"] == str(img_file)

    def test_analyze_raises_when_file_not_found(self):
        analyzer = UserImageAnalyzer(image_path="/nonexistent/image.jpg", api_key="key")

        with patch(PATCH_GENAI):
            with pytest.raises(FileNotFoundError):
                analyzer.analyze()

    def test_analyze_raises_for_unsupported_mime(self, tmp_path):
        txt_file = tmp_path / "file.txt"
        txt_file.write_text("not an image")

        analyzer = UserImageAnalyzer(image_path=str(txt_file), api_key="key")

        with patch(PATCH_GENAI):
            with pytest.raises(ValueError, match="Unsupported image type"):
                analyzer.analyze()
