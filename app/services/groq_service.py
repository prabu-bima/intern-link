import os
import json
import logging
from typing import Dict, Any, Optional

from groq import Groq
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

# Configure the API key
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY is not set. Groq API calls will fail.")


class GroqService:
    """Service wrapper for interacting with the Groq API."""

    def __init__(self, model_name: str = "openai/gpt-oss-20b"):
        """Initialize the Groq service with a specific model."""
        self.model_name = model_name

        try:
            self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")
            self.client = None

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((Exception,)),
        reraise=False
    )
    def _generate_with_retry(self, prompt: str) -> Optional[str]:
        """Call the Groq API with automatic retries for rate limits or server errors."""
        if not self.client:
            raise ValueError("Groq client is not initialized (missing API key?)")

        response = self.client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt}
            ],
            model=self.model_name,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content

    def generate_json(self, prompt: str, fallback: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate content using Groq and parse it as JSON.
        Includes error handling, rate limiting retries, and graceful fallbacks.
        """
        if not fallback:
            fallback = {"error": "Failed to generate content"}

        if not GROQ_API_KEY:
            logger.error("Attempted to call Groq API without GROQ_API_KEY set.")
            return fallback

        try:
            response_text = self._generate_with_retry(prompt)
            if not response_text:
                return fallback

            return json.loads(response_text)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response as JSON: {str(e)}\nResponse: {response_text}")
            return fallback
        except Exception as e:
            logger.error(f"Groq API call completely failed after retries: {str(e)}")
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
groq_service = GroqService()
