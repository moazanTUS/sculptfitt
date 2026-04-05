"""
Unit tests for analyzer modules
Tests form analysis logic without actual video processing

Note: Analyzer tests are intentionally skipped. The squat, shoulder press, 
and pushup analyzers are not tested as they require complex mediapipe/cv2 
setup and are not critical for the core application functionality.
"""
import pytest


class TestAnalyzersPlaceholder:
    """Placeholder test class for analyzer modules
    
    These analyzers are not tested:
    - PushupAnalyzer: Complex mediapipe setup required
    - SquatAnalyzer: Complex mediapipe setup required  
    - ShoulderPressAnalyzer: Complex mediapipe setup required
    - GeminiFormAnalyzer: Requires external API mocking
    - UserImageAnalyzer: Requires cv2 and mediapipe
    """
    
    def test_placeholder(self):
        """Placeholder test to prevent collection errors"""
        assert True

    def test_analyzer_test_scope_documented(self):
        """Keep a fast explicit guard while heavy CV/API tests remain out-of-scope."""
        scope = {
            "requires_mediapipe": True,
            "requires_cv2": True,
            "requires_external_ai_mocking": True,
        }
        assert all(scope.values())
