"""
Unit tests for Clerk authentication module
Tests JWT verification, token extraction, error handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.clerk_auth import require_clerk_user, _get_bearer, _get_signing_key
from fastapi import HTTPException, Request

class TestBearerTokenExtraction:
    """Test token extraction from Authorization header"""
    
    def test_valid_bearer_token(self):
        """Should extract token from valid Authorization header"""
        request = Mock()
        request.headers = {"Authorization": "Bearer test_token_123"}
        
        token = _get_bearer(request)
        assert token == "test_token_123"
    
    def test_missing_authorization_header(self):
        """Should return None when Authorization header missing"""
        request = Mock()
        request.headers = {}
        
        result = _get_bearer(request)
        assert result is None
    
    def test_invalid_bearer_format(self):
        """Should return None when Bearer format incorrect"""
        request = Mock()
        request.headers = {"Authorization": "InvalidFormat token123"}
        
        result = _get_bearer(request)
        assert result is None

class TestJWTVerification:
    """Test JWT token verification logic"""
    
    @patch('backend.clerk_auth.jwt.decode')
    @patch('backend.clerk_auth._get_signing_key')
    @patch('backend.clerk_auth._get_bearer')
    def test_valid_jwt_token(self, mock_bearer, mock_signing, mock_decode):
        """Should return user dict for valid token"""
        mock_bearer.return_value = "valid_token"
        mock_signing.return_value = "signing_key"
        mock_decode.return_value = {"sub": "user_12345"}
        
        request = Mock()
        user_data = require_clerk_user(request)
        
        assert user_data["clerk_user_id"] == "user_12345"
        assert "claims" in user_data
        mock_decode.assert_called_once()
    
    @patch('backend.clerk_auth._get_bearer')
    def test_expired_token(self, mock_bearer):
        """Should raise 401 for expired tokens"""
        from jwt import ExpiredSignatureError
        mock_bearer.return_value = "expired_token"
        
        with patch('backend.clerk_auth.jwt.decode', side_effect=ExpiredSignatureError):
            request = Mock()
            with pytest.raises(HTTPException) as exc:
                require_clerk_user(request)
            assert exc.value.status_code == 401
            assert "invalid" in str(exc.value.detail).lower()
    
    @patch('backend.clerk_auth._get_bearer')
    def test_invalid_signature(self, mock_bearer):
        """Should raise 401 for invalid signature"""
        from jwt import InvalidSignatureError
        mock_bearer.return_value = "invalid_sig_token"
        
        with patch('backend.clerk_auth.jwt.decode', side_effect=InvalidSignatureError):
            request = Mock()
            with pytest.raises(HTTPException) as exc:
                require_clerk_user(request)
            assert exc.value.status_code == 401

class TestSigningKeyRetrieval:
    """Test JWKS endpoint key retrieval"""
    
    @patch('backend.clerk_auth.requests.get')
    def test_successful_jwks_fetch(self, mock_get):
        """Should fetch and cache signing keys"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "keys": [
                {"kid": "key1", "n": "modulus", "e": "exponent", "kty": "RSA", "use": "sig"}
            ]
        }
        mock_get.return_value = mock_response
        
        # Test would require mocking PyJWK - simplified for demo
        # In real tests, you'd verify the key is properly constructed
    
    @patch('backend.clerk_auth.requests.get')
    def test_jwks_fetch_failure(self, mock_get):
        """Should handle JWKS endpoint failures gracefully"""
        mock_get.side_effect = Exception("Network error")
        
        # Should raise or handle gracefully
        # Implementation depends on your error handling strategy
