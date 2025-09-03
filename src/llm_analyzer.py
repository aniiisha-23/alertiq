"""
LLM analyzer module for processing alert emails using Gemini AI.
Analyzes email content and determines appropriate actions.
"""

import json
from typing import Optional

import google.generativeai as genai
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import config
from .models import EmailData, LLMAnalysis, ActionType


class LLMAnalyzer:
    """LLM analyzer using Gemini AI for email content analysis."""

    def __init__(self):
        self.model = None
        self._setup_gemini()

    def _setup_gemini(self):
        """Initialize Gemini AI model."""
        try:
            genai.configure(api_key=config.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini AI model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            raise

    @retry(
        stop=stop_after_attempt(config.retry_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def analyze_email(self, email_data: EmailData) -> Optional[LLMAnalysis]:
        """
        Analyze email content using Gemini AI to determine action.

        Args:
            email_data: EmailData object containing email information

        Returns:
            LLMAnalysis object with action and reason, or None if analysis fails
        """
        try:
            prompt = self._create_analysis_prompt(email_data)

            logger.info(f"Analyzing email: {email_data.subject}")

            # Generate response from Gemini
            response = self.model.generate_content(prompt)

            if not response.text:
                logger.error("Empty response from Gemini AI")
                return None

            # Parse the JSON response
            analysis = self._parse_gemini_response(response.text)

            if analysis:
                logger.info(f"Analysis complete - Action: {analysis.action}, Reason: {analysis.reason}")

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing email {email_data.message_id}: {e}")
            return None

    def _create_analysis_prompt(self, email_data: EmailData) -> str:
        """
        Create a comprehensive prompt for Gemini AI analysis.

        Args:
            email_data: EmailData object

        Returns:
            Formatted prompt string
        """
        prompt = f"""
You are an expert system administrator analyzing alert emails to determine the appropriate action.

Please analyze the following alert email and determine what action should be taken:

EMAIL DETAILS:
Subject: {email_data.subject}
Sender: {email_data.sender}
Received: {email_data.received_date}

EMAIL BODY:
{email_data.body}

INSTRUCTIONS:
Based on the alert content, determine ONE of these three actions:

1. "Re-hit" - If this appears to be a temporary issue that can be resolved by retrying the process
   Examples: timeout errors, temporary network issues, rate limiting, temporary service unavailability

2. "Backend" - If this appears to be a backend infrastructure or configuration issue
   Examples: database connection issues, server errors, service configuration problems, resource exhaustion

3. "Code" - If this appears to be a software bug or code-related issue that requires development intervention
   Examples: application errors, logic bugs, null pointer exceptions, syntax errors, failed deployments

RESPONSE FORMAT:
You must respond with a valid JSON object in exactly this format:
{{
    "action": "Re-hit" | "Backend" | "Code",
    "reason": "Detailed explanation of why this action was chosen (2-3 sentences)",
    "confidence": 0.85
}}

IMPORTANT:
- Only respond with the JSON object, no additional text
- The action must be exactly one of: "Re-hit", "Backend", or "Code"
- The reason should be clear and actionable
- Confidence should be between 0.0 and 1.0
- Focus on the technical indicators in the alert to make your decision

Analyze the alert now:
"""
        return prompt

    def _parse_gemini_response(self, response_text: str) -> Optional[LLMAnalysis]:
        """
        Parse Gemini AI response and create LLMAnalysis object.

        Args:
            response_text: Raw response text from Gemini

        Returns:
            LLMAnalysis object or None if parsing fails
        """
        try:
            # Clean the response text
            response_text = response_text.strip()

            # Try to extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                logger.error("No JSON found in Gemini response")
                return None

            json_text = response_text[json_start:json_end]

            # Parse JSON
            parsed_response = json.loads(json_text)

            # Validate required fields
            if 'action' not in parsed_response or 'reason' not in parsed_response:
                logger.error("Missing required fields in Gemini response")
                return None

            # Validate action type
            action = parsed_response['action']
            if action not in [e.value for e in ActionType]:
                logger.error(f"Invalid action type: {action}")
                return None

            # Create LLMAnalysis object
            analysis = LLMAnalysis(
                action=ActionType(action),
                reason=parsed_response['reason'],
                confidence=parsed_response.get('confidence', 0.8)
            )

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.debug(f"Response text: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return None

    def analyze_batch(self, emails: list[EmailData]) -> dict[str, Optional[LLMAnalysis]]:
        """
        Analyze a batch of emails.

        Args:
            emails: List of EmailData objects

        Returns:
            Dictionary mapping message_id to LLMAnalysis results
        """
        results = {}

        for email_data in emails:
            try:
                analysis = self.analyze_email(email_data)
                results[email_data.message_id] = analysis
            except Exception as e:
                logger.error(f"Error analyzing email {email_data.message_id}: {e}")
                results[email_data.message_id] = None

        return results

    def get_analysis_summary(self, analysis: LLMAnalysis) -> str:
        """
        Get a human-readable summary of the analysis.

        Args:
            analysis: LLMAnalysis object

        Returns:
            Formatted summary string
        """
        confidence_desc = "high" if analysis.confidence > 0.8 else "medium" if analysis.confidence > 0.6 else "low"

        return f"""
Analysis Summary:
- Recommended Action: {analysis.action}
- Confidence: {confidence_desc} ({analysis.confidence:.2f})
- Reasoning: {analysis.reason}
"""
