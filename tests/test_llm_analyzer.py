"""
Tests for the LLM analyzer module.
"""

import json
from unittest.mock import Mock, patch

import pytest

from src.llm_analyzer import LLMAnalyzer
from src.models import ActionType


class TestLLMAnalyzer:
    """Tests for LLMAnalyzer class."""

    @patch('src.llm_analyzer.genai')
    def test_setup_gemini(self, mock_genai, test_config):
        """Test Gemini AI setup."""
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model

        analyzer = LLMAnalyzer()

        mock_genai.configure.assert_called_once_with(api_key="test_api_key")
        mock_genai.GenerativeModel.assert_called_once_with('gemini-pro')
        assert analyzer.model == mock_model

    @patch('src.llm_analyzer.genai')
    def test_analyze_email_success(self, mock_genai, test_config, sample_email_data):
        """Test successful email analysis."""
        # Setup mock
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "action": "Backend",
            "reason": "Database connection timeout indicates infrastructure issue",
            "confidence": 0.85
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        analyzer = LLMAnalyzer()
        result = analyzer.analyze_email(sample_email_data)

        assert result is not None
        assert result.action == ActionType.BACKEND
        assert "infrastructure issue" in result.reason
        assert result.confidence == 0.85

    @patch('src.llm_analyzer.genai')
    def test_analyze_email_invalid_json(self, mock_genai, test_config, sample_email_data):
        """Test handling of invalid JSON response."""
        # Setup mock with invalid JSON
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "This is not valid JSON"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        analyzer = LLMAnalyzer()
        result = analyzer.analyze_email(sample_email_data)

        assert result is None

    @patch('src.llm_analyzer.genai')
    def test_analyze_email_invalid_action(self, mock_genai, test_config, sample_email_data):
        """Test handling of invalid action type."""
        # Setup mock with invalid action
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "action": "InvalidAction",
            "reason": "Some reason",
            "confidence": 0.85
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        analyzer = LLMAnalyzer()
        result = analyzer.analyze_email(sample_email_data)

        assert result is None

    def test_create_analysis_prompt(self, test_config, sample_email_data):
        """Test analysis prompt creation."""
        with patch('src.llm_analyzer.genai'):
            analyzer = LLMAnalyzer()
            prompt = analyzer._create_analysis_prompt(sample_email_data)

            assert sample_email_data.subject in prompt
            assert sample_email_data.body in prompt
            assert "Re-hit" in prompt
            assert "Backend" in prompt
            assert "Code" in prompt
            assert "JSON" in prompt

    def test_parse_gemini_response_success(self, test_config):
        """Test successful parsing of Gemini response."""
        with patch('src.llm_analyzer.genai'):
            analyzer = LLMAnalyzer()

            response_text = '''
            Some text before
            {
                "action": "Code",
                "reason": "Application error in user authentication module",
                "confidence": 0.92
            }
            Some text after
            '''

            result = analyzer._parse_gemini_response(response_text)

            assert result is not None
            assert result.action == ActionType.CODE
            assert "authentication module" in result.reason
            assert result.confidence == 0.92

    @patch('src.llm_analyzer.genai')
    def test_analyze_batch(self, mock_genai, test_config, sample_email_data):
        """Test batch analysis of emails."""
        # Setup mock
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            "action": "Re-hit",
            "reason": "Temporary network issue",
            "confidence": 0.75
        })
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        analyzer = LLMAnalyzer()

        # Create multiple test emails
        emails = [sample_email_data]
        results = analyzer.analyze_batch(emails)

        assert len(results) == 1
        assert sample_email_data.message_id in results
        assert results[sample_email_data.message_id] is not None
        assert results[sample_email_data.message_id].action == ActionType.RE_HIT
