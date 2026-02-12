# profiles/services/ai_service.py

import json
import logging
from django.conf import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class CourseFilterAI:
    def __init__(self):
        # Using fast + cheap model (best for this use case)
        self.model = "gpt-4o-mini"

    def process_student_profile(self, profile_data, course_sample):
        """
        Process student profile and generate intelligent course filters
        """

        prompt = f"""
You are a course filtering AI.

Analyze the student profile and return ONLY a valid JSON object.

Student Profile:
- Preferred Countries: {', '.join(profile_data.get('countries', []))}
- Target Degree: {profile_data.get('degree', '')}
- Fields of Interest: {', '.join(profile_data.get('fields', []))}
- Completed Degree: {profile_data.get('completedDegree', '')}
- CGPA: {profile_data.get('cgpa', 0)}/10
- Graduation Year: {profile_data.get('gradYear', '')}
- Budget: ₹{profile_data.get('budget', [0])[0]} Lakhs per year

Return ONLY this JSON structure:

{{
  "country": "",
  "level": "",
  "course": "",
  "duration": "",
  "maxBudgetUSD": null,
  "searchQuery": ""
}}

No explanation.
No markdown.
Only raw JSON.
"""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            response_text = response.choices[0].message.content.strip()

            logger.info(f"OpenAI response: {response_text}")

            filters = json.loads(response_text)

            return {
                "success": True,
                "filters": filters
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to parse AI response: {str(e)}",
                "raw_response": response_text
            }

        except Exception as e:
            logger.error(f"OpenAI error: {str(e)}")
            return {
                "success": False,
                "error": f"AI processing failed: {str(e)}"
            }
