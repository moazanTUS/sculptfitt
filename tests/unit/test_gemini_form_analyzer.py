"""
Unit tests for GeminiFormAnalyzer.
All external I/O (cv2, genai, tempfile, os) is mocked.
"""
import base64
import io
import os
from unittest.mock import Mock, MagicMock, patch, PropertyMock

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_frame():
    """Return a minimal 10x10 BGR numpy array frame."""
    return np.zeros((10, 10, 3), dtype=np.uint8)


def _b64_jpeg():
    """Return a valid base64-encoded 1x1 JPEG string."""
    import cv2
    frame = _make_fake_frame()
    _, buf = cv2.imencode('.jpg', frame)
    return base64.b64encode(buf).decode("utf-8")


def _make_genai_response(text="Great form!"):
    """Build a minimal mock genai response."""
    part = Mock()
    part.text = text
    content = Mock()
    content.parts = [part]
    candidate = Mock()
    candidate.content = content
    candidate.finish_reason = "STOP"
    response = Mock()
    response.candidates = [candidate]
    response.text = text
    return response


# ---------------------------------------------------------------------------
# Patch targets
# ---------------------------------------------------------------------------

PATCH_CV2 = "backend.analyzers.gemini_form_analyzer.cv2"
PATCH_GENAI = "backend.analyzers.gemini_form_analyzer.genai"
PATCH_TEMPFILE = "backend.analyzers.gemini_form_analyzer.tempfile"
PATCH_OS_REMOVE = "backend.analyzers.gemini_form_analyzer.os.remove"
PATCH_OS_EXISTS = "backend.analyzers.gemini_form_analyzer.os.path.exists"
PATCH_NP = "backend.analyzers.gemini_form_analyzer.np"
PATCH_HAS_MP = "backend.analyzers.gemini_form_analyzer.HAS_MEDIAPIPE"


def _make_analyzer(video_path="/fake/video.mp4", **kwargs):
    """Build a GeminiFormAnalyzer with all external calls mocked."""
    mock_client = Mock()
    mock_model_list = [Mock(name="models/gemini-2.5-flash")]
    mock_model_list[0].name = "models/gemini-2.5-flash"
    mock_client.models.list.return_value = mock_model_list

    with patch(PATCH_OS_EXISTS, return_value=True), \
         patch(PATCH_GENAI) as mock_genai, \
         patch(PATCH_HAS_MP, False):
        mock_genai.Client.return_value = mock_client
        from backend.analyzers.gemini_form_analyzer import GeminiFormAnalyzer
        analyzer = GeminiFormAnalyzer(
            video_path=video_path,
            api_key="fake-key",
            num_frames=3,
            **kwargs
        )
    return analyzer, mock_client


# ---------------------------------------------------------------------------
# __init__ tests
# ---------------------------------------------------------------------------

class TestGeminiFormAnalyzerInit:
    def test_init_with_video_path(self):
        analyzer, _ = _make_analyzer()
        assert analyzer.video_path == "/fake/video.mp4"
        assert not analyzer.is_temp

    def test_init_with_video_bytes(self):
        fake_bytes = io.BytesIO(b"\x00" * 100)
        mock_tmp = Mock()
        mock_tmp.name = "/tmp/fake.mp4"

        mock_client = Mock()
        mock_model_list = [Mock()]
        mock_model_list[0].name = "models/gemini-2.5-flash"
        mock_client.models.list.return_value = mock_model_list

        with patch(PATCH_TEMPFILE) as mock_tf, \
             patch(PATCH_GENAI) as mock_genai, \
             patch(PATCH_HAS_MP, False):
            mock_tf.NamedTemporaryFile.return_value = mock_tmp
            mock_genai.Client.return_value = mock_client
            from backend.analyzers.gemini_form_analyzer import GeminiFormAnalyzer
            analyzer = GeminiFormAnalyzer(video_bytes=fake_bytes, api_key="key")

        assert analyzer.is_temp is True
        assert analyzer.video_path == "/tmp/fake.mp4"

    def test_init_raises_without_path_or_bytes(self):
        with patch(PATCH_GENAI), patch(PATCH_HAS_MP, False):
            from backend.analyzers.gemini_form_analyzer import GeminiFormAnalyzer
            with pytest.raises(ValueError, match="Must provide"):
                GeminiFormAnalyzer(api_key="key")

    def test_init_raises_when_file_not_found(self):
        with patch(PATCH_OS_EXISTS, return_value=False), \
             patch(PATCH_GENAI), patch(PATCH_HAS_MP, False):
            from backend.analyzers.gemini_form_analyzer import GeminiFormAnalyzer
            with pytest.raises(FileNotFoundError):
                GeminiFormAnalyzer(video_path="/nonexistent.mp4", api_key="key")

    def test_init_raises_when_no_api_key(self):
        import os as _os
        original = _os.environ.pop("GEMINI_API_KEY", None)
        try:
            with patch(PATCH_OS_EXISTS, return_value=True), \
                 patch(PATCH_GENAI), patch(PATCH_HAS_MP, False):
                from backend.analyzers.gemini_form_analyzer import GeminiFormAnalyzer
                with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                    GeminiFormAnalyzer(video_path="/fake.mp4")
        finally:
            if original is not None:
                _os.environ["GEMINI_API_KEY"] = original

    def test_init_model_selection_fallback(self):
        """When model listing fails, falls back to gemini-2.5-flash."""
        mock_client = Mock()
        mock_client.models.list.side_effect = Exception("no models")

        with patch(PATCH_OS_EXISTS, return_value=True), \
             patch(PATCH_GENAI) as mock_genai, \
             patch(PATCH_HAS_MP, False):
            mock_genai.Client.return_value = mock_client
            from backend.analyzers.gemini_form_analyzer import GeminiFormAnalyzer
            analyzer = GeminiFormAnalyzer(video_path="/fake.mp4", api_key="key")

        assert analyzer.model == "gemini-2.5-flash"

    def test_init_model_prefers_flash(self):
        """When multiple models listed, picks gemini-2.5-flash over others."""
        mock_client = Mock()
        models = []
        for name in ["models/gemini-embedding-001", "models/gemini-2.5-flash", "models/gemini-2.0-flash"]:
            m = Mock()
            m.name = name
            models.append(m)
        mock_client.models.list.return_value = models

        with patch(PATCH_OS_EXISTS, return_value=True), \
             patch(PATCH_GENAI) as mock_genai, \
             patch(PATCH_HAS_MP, False):
            mock_genai.Client.return_value = mock_client
            from backend.analyzers.gemini_form_analyzer import GeminiFormAnalyzer
            analyzer = GeminiFormAnalyzer(video_path="/fake.mp4", api_key="key")

        assert "gemini-2.5-flash" in analyzer.model


# ---------------------------------------------------------------------------
# extract_frames
# ---------------------------------------------------------------------------

class TestExtractFrames:
    def test_extract_frames_returns_frames(self):
        analyzer, _ = _make_analyzer(rep_count=3)

        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {0: 30.0, 7: 90}[prop]  # fps=30, frames=90
        mock_cap.read.return_value = (True, _make_fake_frame())

        with patch(PATCH_CV2) as mock_cv2, \
             patch("backend.analyzers.gemini_form_analyzer.np", np):
            mock_cv2.VideoCapture.return_value = mock_cap
            mock_cv2.CAP_PROP_FPS = 0
            mock_cv2.CAP_PROP_FRAME_COUNT = 7
            frames = analyzer.extract_frames()

        assert len(frames) > 0

    def test_extract_frames_raises_when_cannot_open(self):
        analyzer, _ = _make_analyzer()

        mock_cap = Mock()
        mock_cap.isOpened.return_value = False

        with patch(PATCH_CV2) as mock_cv2:
            mock_cv2.VideoCapture.return_value = mock_cap
            mock_cv2.CAP_PROP_FPS = 0
            mock_cv2.CAP_PROP_FRAME_COUNT = 7
            with pytest.raises(FileNotFoundError):
                analyzer.extract_frames()


# ---------------------------------------------------------------------------
# frames_to_base64
# ---------------------------------------------------------------------------

class TestFramesToBase64:
    def test_converts_frames_to_base64_strings(self):
        analyzer, _ = _make_analyzer()
        frames = [_make_fake_frame(), _make_fake_frame()]

        with patch(PATCH_CV2) as mock_cv2:
            mock_cv2.imencode.return_value = (True, np.frombuffer(b"\xff\xd8\xff", dtype=np.uint8))
            result = analyzer.frames_to_base64(frames)

        assert len(result) == 2
        for item in result:
            assert isinstance(item, str)


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------

class TestAnalyze:
    def test_analyze_success(self):
        analyzer, mock_client = _make_analyzer()
        response = _make_genai_response("Good job! Keep your back straight.")
        mock_client.models.generate_content.return_value = response

        with patch.object(analyzer, "extract_frames", return_value=[_make_fake_frame()]), \
             patch.object(analyzer, "frames_to_base64", return_value=[_b64_jpeg()]), \
             patch(PATCH_GENAI) as mock_genai:
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            analyzer.client = mock_client
            result = analyzer.analyze(exercise="Squat")

        assert result["success"] is True
        assert "Squat" in result["exercise"]
        assert result["feedback"] == "Good job! Keep your back straight."

    def test_analyze_no_frames_returns_error(self):
        analyzer, _ = _make_analyzer()

        with patch.object(analyzer, "extract_frames", return_value=[]):
            result = analyzer.analyze()

        assert result["success"] is False
        assert "frames" in result["error"].lower()

    def test_analyze_no_candidates_returns_error(self):
        analyzer, mock_client = _make_analyzer()
        response = Mock()
        response.candidates = []

        mock_client.models.generate_content.return_value = response

        with patch.object(analyzer, "extract_frames", return_value=[_make_fake_frame()]), \
             patch.object(analyzer, "frames_to_base64", return_value=[_b64_jpeg()]), \
             patch(PATCH_GENAI) as mock_genai:
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            analyzer.client = mock_client
            result = analyzer.analyze()

        assert result["success"] is False
        assert "no candidates" in result["error"].lower()

    def test_analyze_empty_candidate_content_returns_error(self):
        analyzer, mock_client = _make_analyzer()

        candidate = Mock()
        candidate.content = None
        candidate.finish_reason = "SAFETY"
        response = Mock()
        response.candidates = [candidate]

        mock_client.models.generate_content.return_value = response

        with patch.object(analyzer, "extract_frames", return_value=[_make_fake_frame()]), \
             patch.object(analyzer, "frames_to_base64", return_value=[_b64_jpeg()]), \
             patch(PATCH_GENAI) as mock_genai:
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            analyzer.client = mock_client
            result = analyzer.analyze()

        assert result["success"] is False

    def test_analyze_response_text_fallback_via_parts(self):
        """When response.text raises on the actual access, text is extracted from parts.
        Use a side_effect list: first call (hasattr) returns '' to signal presence;
        second call (actual read inside try) raises ValueError to trigger fallback."""
        analyzer, mock_client = _make_analyzer()

        feedback = "Nice work!"
        part = Mock()
        part.text = feedback
        content = Mock()
        content.parts = [part]
        candidate = Mock()
        candidate.content = content
        candidate.finish_reason = "STOP"

        response = Mock()
        response.candidates = [candidate]
        # First access (hasattr check) returns '' so hasattr is True;
        # second access (assignment inside try) raises ValueError → fallback to parts.
        type(response).text = PropertyMock(side_effect=["", ValueError("blocked")])

        mock_client.models.generate_content.return_value = response

        with patch.object(analyzer, "extract_frames", return_value=[_make_fake_frame()]), \
             patch.object(analyzer, "frames_to_base64", return_value=[_b64_jpeg()]), \
             patch(PATCH_GENAI) as mock_genai:
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            analyzer.client = mock_client
            result = analyzer.analyze()

        assert result["success"] is True
        assert result["feedback"] == feedback

    def test_analyze_generate_content_exception_returns_error(self):
        analyzer, mock_client = _make_analyzer()
        mock_client.models.generate_content.side_effect = Exception("API error")

        with patch.object(analyzer, "extract_frames", return_value=[_make_fake_frame()]), \
             patch.object(analyzer, "frames_to_base64", return_value=[_b64_jpeg()]), \
             patch(PATCH_GENAI) as mock_genai:
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            analyzer.client = mock_client
            result = analyzer.analyze()

        assert result["success"] is False
        assert "API error" in result["error"]

    def test_analyze_includes_rep_count_when_set(self):
        """_detected_rep_count is normally set by extract_frames; set it manually
        since extract_frames is mocked here."""
        analyzer, mock_client = _make_analyzer(rep_count=5)
        analyzer._detected_rep_count = 5  # simulate what extract_frames would set
        response = _make_genai_response("Solid reps!")
        mock_client.models.generate_content.return_value = response

        with patch.object(analyzer, "extract_frames", return_value=[_make_fake_frame()]), \
             patch.object(analyzer, "frames_to_base64", return_value=[_b64_jpeg()]), \
             patch(PATCH_GENAI) as mock_genai:
            mock_genai.types.Blob = Mock(return_value=Mock())
            mock_genai.types.Part = Mock(return_value=Mock())
            analyzer.client = mock_client
            result = analyzer.analyze(exercise="Deadlift")

        assert result.get("detected_reps") == 5


# ---------------------------------------------------------------------------
# _cleanup
# ---------------------------------------------------------------------------

class TestCleanup:
    def test_cleanup_removes_temp_file(self):
        analyzer, _ = _make_analyzer()
        analyzer.is_temp = True
        analyzer.temp_file = Mock()
        analyzer.temp_file.name = "/tmp/fakevid.mp4"

        with patch(PATCH_OS_REMOVE) as mock_rm:
            analyzer._cleanup()

        mock_rm.assert_called_once_with("/tmp/fakevid.mp4")

    def test_cleanup_noop_for_non_temp(self):
        analyzer, _ = _make_analyzer()
        analyzer.is_temp = False

        with patch(PATCH_OS_REMOVE) as mock_rm:
            analyzer._cleanup()

        mock_rm.assert_not_called()

    def test_cleanup_handles_remove_error_gracefully(self):
        analyzer, _ = _make_analyzer()
        analyzer.is_temp = True
        analyzer.temp_file = Mock()
        analyzer.temp_file.name = "/tmp/fakevid.mp4"

        with patch(PATCH_OS_REMOVE, side_effect=OSError("perm denied")):
            analyzer._cleanup()  # should not raise
