import os
import json
import logging
from typing import Dict, Any, Optional

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, InternalServerError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

# Configure the API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not set. Gemini API calls will fail.")


class GeminiService:
    """Service wrapper for interacting with the Google Gemini API."""

    def __init__(self, model_name: str = "gemini-3.5-flash"):
        """Initialize the Gemini service with a specific model."""
        self.model_name = model_name
        
        # Configure model with JSON response type as default for our use cases
        self.generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            self.model = None

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable, InternalServerError)),
        reraise=False
    )
    def _generate_with_retry(self, prompt: str) -> Optional[str]:
        """Call the Gemini API with automatic retries for rate limits or server errors."""
        if not self.model:
            raise ValueError("Gemini model is not initialized (missing API key?)")
        
        response = self.model.generate_content(prompt)
        return response.text

    def generate_json(self, prompt: str, fallback: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate content using Gemini and parse it as JSON.
        Includes error handling, rate limiting retries, and graceful fallbacks.
        """
        if not fallback:
            fallback = {"error": "Failed to generate content"}

        if not GEMINI_API_KEY:
            logger.error("Attempted to call Gemini API without GEMINI_API_KEY set.")
            return fallback

        try:
            response_text = self._generate_with_retry(prompt)
            if not response_text:
                return fallback
                
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {str(e)}\nResponse: {response_text}")
            return fallback
        except Exception as e:
            logger.error(f"Gemini API call completely failed after retries: {str(e)}")
            return fallback


class AIPromptTemplates:
    """Structured prompt templates for AI features."""

    @staticmethod
    def ai_skill_match(student_data: Dict[str, Any], internship_data: Dict[str, Any]) -> str:
        """Prompt template for matching a student to an internship."""
        return f"""
        You are an expert HR Technology Assistant that matches students with internship opportunities.
        Analyze the following student profile and internship requirements to determine how well they match.

        STUDENT PROFILE:
        {json.dumps(student_data, indent=2)}

        INTERNSHIP REQUIREMENTS:
        {json.dumps(internship_data, indent=2)}

        Provide your analysis in the following strict JSON format:
        {{
            "match_percentage": <int, 0-100 based on how well the skills and tech stack align>,
            "matching_skills": [<list of strings, skills the student has that the internship requires>],
            "missing_skills": [<list of strings, required skills the student is missing>],
            "explanation": "<string, a 2-3 sentence paragraph explaining the match percentage and overall fit. MUST BE IN BAHASA INDONESIA>",
            "suggested_skills": [<list of strings, 2-4 skills the student should learn to be a better fit>]
        }}
        """

    @staticmethod
    def job_recommendation(student_data: Dict[str, Any], available_internships: list[Dict[str, Any]]) -> str:
        """Prompt template for recommending the best internships to a student."""
        return f"""
        You are an expert HR Technology Assistant. 
        Based on the student's profile, recommend the top 3 best matching internships from the available list.

        STUDENT PROFILE:
        {json.dumps(student_data, indent=2)}

        AVAILABLE INTERNSHIPS:
        {json.dumps(available_internships, indent=2)}

        Provide your analysis in the following strict JSON format:
        {{
            "recommendations": [
                {{
                    "internship_id": <id of the recommended internship>,
                    "match_percentage": <int, 0-100>,
                    "reasoning": "<string, brief 1-2 sentence explanation why this is a good fit. MUST BE IN BAHASA INDONESIA>"
                }}
            ]
        }}
        """

# Singleton instance for easy importing
gemini_service = GeminiService()
